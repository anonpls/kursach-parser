import re
from hashlib import sha1

import scrapy


class DnsSpider(scrapy.Spider):
    name = "dns"
    allowed_domains = ["dns-shop.ru", "www.dns-shop.ru"]
    start_urls = ["https://www.dns-shop.ru/catalog/17a8a01d16404e77/smartfony/"]

    def parse(self, response):
        for product in response.css("div.catalog-product, div[data-code]"):
            url = response.urljoin(
                product.css(
                    "a.catalog-product__name::attr(href), "
                    "a.catalog-product__name span::attr(href), "
                    "a[href*='/product/']::attr(href)"
                ).get("")
            )
            name = " ".join(
                text.strip()
                for text in product.css(
                    "a.catalog-product__name span::text, "
                    "a.catalog-product__name::text, "
                    "a[href*='/product/']::text"
                ).getall()
                if text.strip()
            )
            price_text = " ".join(
                product.css(
                    "div.product-buy__price::text, "
                    "div.catalog-product__price::text, "
                    "[class*='price']::text"
                ).getall()
            )
            price = self._clean_price(price_text)
            external_id = product.attrib.get("data-code") or self._external_id(url)

            if external_id and name and url and price:
                yield {
                    "external_id": external_id,
                    "name": name,
                    "url": url,
                    "price": price,
                }

    @staticmethod
    def _clean_price(value: str) -> str:
        normalized = re.sub(r"[^\d,.]", "", value).replace(",", ".")
        match = re.search(r"\d+(?:\.\d+)?", normalized)
        return match.group(0) if match else ""

    @staticmethod
    def _external_id(url: str) -> str:
        parts = [part for part in url.split("/") if part]
        if "product" in parts:
            index = parts.index("product")
            if index + 1 < len(parts):
                return parts[index + 1]
        return sha1(url.encode("utf-8")).hexdigest()
