import re
from hashlib import sha1

import scrapy


class DicentreSpider(scrapy.Spider):
    name = "dicentre"
    allowed_domains = ["dicentre.ru", "www.dicentre.ru"]
    start_urls = ["https://dicentre.ru/sotovye-telefony/"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
        "DOWNLOAD_TIMEOUT": 30,
        "HTTPERROR_ALLOWED_CODES": [401, 403],
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    }

    def parse(self, response):
        if response.status in {401, 403}:
            self.logger.error(
                "%s вернул HTTP %s. Сайт заблокировал автоматический запрос или требует браузерную проверку.",
                response.url,
                response.status,
            )
            return

        products = response.css(".product-list .product-tile__outer") or response.css(".js-product-item.product-tile")

        for product in products:
            url = response.urljoin(
                product.css(
                    ".product-tile__name a::attr(href), "
                    ".product-tile__image a::attr(href), "
                    "a[href*='/sotovye-telefony/']::attr(href)"
                ).get("")
            )
            name = self._clean_text(
                product.css(
                    ".product-tile__name a::text, "
                    ".product-tile__name a::attr(title), "
                    "form.js-add-to-cart::attr(data-name)"
                ).getall()
            )
            price = self._clean_price(
                product.css("form.js-add-to-cart::attr(data-price)").get("")
                or " ".join(product.css(".product-tile__price .price::text, .price::text").getall())
            )
            external_id = (
                product.css("input[name='product_id']::attr(value)").get()
                or product.css("[data-product-id]::attr(data-product-id), [data-product]::attr(data-product)").get()
                or self._external_id(url)
            )

            if external_id and name and url and price:
                yield {
                    "external_id": external_id,
                    "name": name,
                    "url": url,
                    "price": price,
                }

    @staticmethod
    def _clean_text(values: list[str]) -> str:
        seen = []
        for value in values:
            stripped = value.strip()
            if stripped and stripped not in seen:
                seen.append(stripped)
        return " ".join(seen)

    @staticmethod
    def _clean_price(value: str) -> str:
        normalized = re.sub(r"[^\d,.]", "", value).replace(",", ".")
        match = re.search(r"\d+(?:\.\d+)?", normalized)
        return match.group(0) if match else ""

    @staticmethod
    def _external_id(url: str) -> str:
        return sha1(url.encode("utf-8")).hexdigest() if url else ""
