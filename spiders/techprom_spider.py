import re
from hashlib import sha1
from urllib.parse import parse_qs, urlparse

import scrapy


class TechpromSpider(scrapy.Spider):
    name = "techprom"
    allowed_domains = ["techprom.ru", "www.techprom.ru"]
    start_urls = [
        "https://www.techprom.ru/catalog/smartfony_planshety_i_gadzhety/smartfony_i_gadzhety/smartfony/"
    ]

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

    def __init__(self, max_pages: str | int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = max(1, int(max_pages or 1))

    def parse(self, response):
        if response.status in {401, 403}:
            self.logger.error(
                "%s вернул HTTP %s. Сайт заблокировал автоматический запрос или требует браузерную проверку.",
                response.url,
                response.status,
            )
            return

        products = response.css(".products-list.card .product-wrap") or response.css(".product-wrap")

        for product in products:
            url = response.urljoin(product.css("a.name::attr(href), a.img-product-link::attr(href)").get(""))
            name = self._clean_text(product.css("a.name::text, a.name *::text").getall())
            price = self._clean_price(
                " ".join(
                    product.css(
                        ".price span[id*='_price']::text, "
                        ".price-container .price span::text, "
                        ".price .measure::text, "
                        ".price::text"
                    ).getall()
                )
            )
            external_id = self._external_id(
                url,
                product.css("div[id^='bx_'][data-entity='item']::attr(id), div[id^='bx_']::attr(id)").get(""),
            )

            if external_id and name and url and price:
                yield {
                    "external_id": external_id,
                    "name": name,
                    "url": url,
                    "price": price,
                }

        current_page = self._page_number(response.url)
        if current_page < self.max_pages:
            next_page = self._next_page_url(response)
            if next_page:
                yield response.follow(next_page, callback=self.parse)

    @staticmethod
    def _clean_text(values: list[str]) -> str:
        return " ".join(value.strip() for value in values if value.strip())

    @staticmethod
    def _clean_price(value: str) -> str:
        normalized = re.sub(r"[^\d,.]", "", value).replace(",", ".")
        match = re.search(r"\d+(?:\.\d+)?", normalized)
        return match.group(0) if match else ""

    @staticmethod
    def _external_id(url: str, bitrix_id: str = "") -> str:
        parts = [part for part in url.split("/") if part]
        if parts and parts[-1].isdigit():
            return parts[-1]

        match = re.search(r"_([0-9]+)_[0-9a-f]{32}$", bitrix_id)
        if match:
            return match.group(1)

        return sha1(url.encode("utf-8")).hexdigest() if url else ""

    @staticmethod
    def _next_page_url(response) -> str:
        current_page = TechpromSpider._page_number(response.url)
        candidates = response.css(
            ".pagination-bottom a.next::attr(href), "
            ".pagination a.next::attr(href), "
            ".pagination a[href*='PAGEN_1=']::attr(href)"
        ).getall()
        return TechpromSpider._next_numbered_url(response, candidates, "PAGEN_1", current_page)

    @staticmethod
    def _next_numbered_url(response, candidates: list[str], query_key: str, current_page: int) -> str:
        numbered_urls = []
        for href in candidates:
            absolute_url = response.urljoin(href)
            values = parse_qs(urlparse(absolute_url).query).get(query_key, [])
            try:
                page = int(values[0])
            except (IndexError, TypeError, ValueError):
                continue
            if page > current_page:
                numbered_urls.append((page, absolute_url))
        return min(numbered_urls)[1] if numbered_urls else ""

    @staticmethod
    def _page_number(url: str) -> int:
        page_values = parse_qs(urlparse(url).query).get("PAGEN_1", ["1"])
        try:
            return int(page_values[0])
        except (TypeError, ValueError):
            return 1
