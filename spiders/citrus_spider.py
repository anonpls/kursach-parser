import scrapy


class CitrusSpider(scrapy.Spider):
    name = "citrus"
    allowed_domains = ["ctrs.com.ua", "www.ctrs.com.ua"]
    start_urls = ["https://www.ctrs.com.ua/smartfony/"]

    def parse(self, response):
        for product in response.css("div.product-card"):
            yield {
                "external_id": product.attrib.get("data-product-id"),
                "name": product.css("a.product-card__name::text").get(default="").strip(),
                "url": response.urljoin(product.css("a.product-card__name::attr(href)").get("")),
                "price": product.css("span.price__value::text").get(default="0").replace(" ", ""),
            }
