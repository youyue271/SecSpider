from requestSpider.base_spider import BaseSpider


class AnquankeSpider(BaseSpider):
    """安全客社区爬虫"""

    def __init__(self):
        super().__init__('anquanke')

    def generate_url(self, post_id):
        return f'https://www.anquanke.com/post/id/{post_id}'

    def parse_title(self, soup):
        title_tag = soup.title
        if not title_tag:
            return "未知标题"
        return title_tag.string.split(" - ")[0]

    def find_content(self, soup):
        return soup.find('div', class_='content')

    def check_category(self, soup):
        tag = soup.find('ul', class_='_56')
        try:
            category = tag.find('li').find('a').string
            return "漏洞情报" in category
        except AttributeError:
            return False
