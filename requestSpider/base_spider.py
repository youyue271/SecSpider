import os
import re
import threading

import markdownify
import requests
from bs4 import BeautifulSoup
import abc


class BaseSpider(metaclass=abc.ABCMeta):
    """爬虫基类，封装通用逻辑"""

    def __init__(self, output_dir):
        self.output_dir = os.path.join("output/", output_dir)
        self.img_dir = os.path.join(self.output_dir, 'img')
        self.record_file = os.path.join(self.output_dir, 'record.txt')
        self.lastId = 0
        os.makedirs(self.img_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def clean_filename(filename):
        """清理文件名中的非法字符"""
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    def get_start_id(self):
        """获取起始ID"""
        if os.path.exists(self.record_file):
            with open(self.record_file, "r", encoding="utf-8") as f:
                return int(f.read())
        return 1

    def save_progress(self):
        """保存进度"""
        post_id = self.lastId
        with open(self.record_file, 'w', encoding='utf-8') as f:
            f.write(str(post_id))
        print(f"[-] 成功保存进度 {post_id} 至 {self.record_file}")

    @abc.abstractmethod
    def generate_url(self, post_id):
        """生成帖子URL（子类必须实现）"""
        raise NotImplementedError

    @abc.abstractmethod
    def parse_title(self, soup):
        """解析标题（子类必须实现）"""
        raise NotImplementedError

    @abc.abstractmethod
    def find_content(self, soup):
        """查找内容区域（子类必须实现）"""
        raise NotImplementedError

    def check_category(self, soup):
        """检查分类是否符合要求（子类必须实现）"""
        # raise NotImplementedError
        return True

    def download_image(self, image_url):
        """下载图片并返回本地路径"""
        local_filename = self.clean_filename(os.path.basename(image_url))
        local_path = os.path.join(self.img_dir, local_filename)

        with requests.get(image_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_path

    def process_post(self, post_id):
        """处理单个帖子"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # 发送请求
            response = requests.get(self.generate_url(post_id), headers=headers)
            response.raise_for_status()
            response.encoding = 'utf-8'

            # 解析内容
            soup = BeautifulSoup(response.text, 'html.parser')
            title = self.parse_title(soup)

            # 分类检查
            if not self.check_category(soup):
                print(f"帖子 {post_id}：{title} 不符合分类要求，不保存")
                return self.lastId

            # 获取内容主体
            content = self.find_content(soup)
            if not content:
                print(f"未找到帖子 {post_id} 的内容")
                return self.lastId

            # 转换Markdown
            markdown_content = markdownify.markdownify(str(content), heading_style='ATX')

            # 处理图片
            for img in content.find_all('img'):
                if img_url := img.get('src'):
                    if img_url.startswith('http'):
                        local_path = self.download_image(img_url)
                        relative_path = os.path.relpath(local_path, self.output_dir)
                        markdown_content = markdown_content.replace(
                            img_url,
                            relative_path.replace('\\', '/')
                        )

            # 保存文件
            valid_title = self.clean_filename(title)
            md_path = os.path.join(self.output_dir, f"{valid_title}.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f'# {title}\n\n{markdown_content}')

            print(f'成功保存帖子 {post_id}: {md_path}')
            return post_id

        except requests.RequestException as e:
            print(f"请求失败 {post_id}: {e}")
            return post_id - 1
        except Exception as e:
            print(f"处理失败 {post_id}: {e}")
            self.save_progress()
            return post_id - 1

    def start_crawl(self, start=1, end=100000):
        """启动爬虫"""
        current_id = self.get_start_id()
        while  current_id <= end:
            try:
                self.lastId = self.process_post(current_id)
                current_id += 1
            except KeyboardInterrupt:
                print("\n用户中断，保存进度...")
                self.save_progress()
                break
        self.save_progress()
