from requestSpider.base_spider import BaseSpider


class HuoxianSpider(BaseSpider):
    """火线社区爬虫"""

    def __init__(self):
        super().__init__('huoxian')

    def generate_url(self, post_id):
        return f'https://zone.huoxian.cn/d/{post_id}'

    def parse_title(self, soup):
        title_tag = soup.title
        if not title_tag:
            return "未知标题"
        return title_tag.string.split(" - ")[0]

    def find_content(self, soup):
        return soup.find('div', class_='Post-body')

    # def check_category(self, soup):
    #     tag = soup.find('ul', class_='_56')
    #     if not tag:
    #         return False
    #     return bool(tag.find('li', string='漏洞情报'))