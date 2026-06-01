import html
import json
import re
from hashlib import sha1

import scrapy


class CitilinkSpider(scrapy.Spider):
    name = "citilink"
    allowed_domains = ["citilink.ru", "www.citilink.ru"]
    start_urls = ["https://www.citilink.ru/catalog/smartfony/"]

    def parse(self, response):
        for product in response.css("div.product_data__gtm-js, div[data-meta-product-id], div[data-params]"):
            params = self._load_params(product.attrib.get("data-params", ""))
            url = response.urljoin(
                product.css(
                    "a[data-meta-name='ProductVerticalSnippet__name']::attr(href), "
                    "a.ProductCardVertical__name::attr(href), "
                    "a[href*='/product/']::attr(href)"
                ).get(params.get("url", ""))
            )
            name = params.get("shortName") or params.get("name") or " ".join(
                text.strip()
                for text in product.css(
                    "a[data-meta-name='ProductVerticalSnippet__name']::text, "
                    "a.ProductCardVertical__name::text, "
                    "a[href*='/product/']::text"
                ).getall()
                if text.strip()
            )
            price = str(params.get("price") or self._clean_price(" ".join(product.css("[class*='price']::text").getall())))
            external_id = str(
                params.get("id")
                or params.get("productId")
                or product.attrib.get("data-meta-product-id")
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
    def _load_params(value: str) -> dict:
        if not value:
            return {}
        try:
            return json.loads(html.unescape(value))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _clean_price(value: str) -> str:
        normalized = re.sub(r"[^\d,.]", "", value).replace(",", ".")
        match = re.search(r"\d+(?:\.\d+)?", normalized)
        return match.group(0) if match else ""

    @staticmethod
    def _external_id(url: str) -> str:
        return sha1(url.encode("utf-8")).hexdigest()
