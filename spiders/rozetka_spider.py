import scrapy


class RozetkaSpider(scrapy.Spider):
    name = "rozetka"
    allowed_domains = ["rozetka.com.ua"]
    start_urls = ["https://rozetka.com.ua/mobile-phones/c80003/"]

    def parse(self, response):
        for product in response.css("div.goods-tile"):
            yield {
                "external_id": product.attrib.get("data-goods-id"),
                "name": product.css("span.goods-tile__title::text").get(default="").strip(),
                "url": response.urljoin(product.css("a.goods-tile__heading::attr(href)").get("")),
                "price": product.css("span.goods-tile__price-value::text").get(default="0").replace(" ", ""),
            }
