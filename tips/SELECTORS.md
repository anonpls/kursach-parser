# CSS Selectors для парсеров смартфонов

## 1. TechProm (`Смартфоны.html`)

### Структура сайта: Bitrix (`magnet`-шаблон)

#### Контейнер продуктов
```css
.products-list.card
```

#### Каждый товар
```css
.product-wrap
```

#### Элементы товара
- **Название товара:**
  ```css
  .product-wrap a.name
  ```

- **Цена:**
  ```css
  .price span[id*="_price"]
  .price-container .price span
  ```

- **Изображение:**
  ```css
  .img-product-link img
  ```
  В HTML часто реальная картинка лежит в `data-src`, а в `src` стоит заглушка.

- **Ссылка на товар:**
  ```css
  .product-wrap a.name
  .product-wrap a.img-product-link
  ```
  атрибут: `href`

- **ID товара:**
  ```css
  .product-wrap div[id^="bx_"][data-entity="item"]
  ```
  атрибут: `id`; в примере ID товара находится между подчёркиваниями: `bx_..._99982_...`.

- **Статус наличия:**
  ```css
  .stock .product-item-quantity
  ```

#### XPath альтернативы
```xpath
//div[contains(@class, 'product-wrap')]
//a[contains(@class, 'name')]
//span[contains(@id, '_price')]
//a[contains(@class, 'img-product-link')]//img
```

---

## 2. DiCENTRE (`Смартфоны и телефоны... DiCENTRE.html`)

### Структура сайта: WebAsyst (`mastershop`-тема)

#### Контейнер продуктов
```css
.product-list.product-list--tile
.js-preview-products
```

#### Каждый товар
```css
.product-tile__outer
.js-product-item.product-tile
```

#### Элементы товара
- **Название товара:**
  ```css
  .product-tile__name a
  ```

- **Цена:**
  ```css
  form.js-add-to-cart::attr(data-price)
  .product-tile__price .price
  ```

- **Изображение:**
  ```css
  .product-tile__image img.js-product-preview-img
  ```

- **Ссылка на товар:**
  ```css
  .product-tile__name a
  .product-tile__image a
  ```
  атрибут: `href`

- **ID товара:**
  ```css
  input[name="product_id"]
  [data-product-id]
  [data-product]
  ```
  атрибуты: `value`, `data-product-id`, `data-product`

- **Статус наличия:**
  ```css
  .product-stock.product-tile__stock
  ```

#### XPath альтернативы
```xpath
//div[contains(@class, 'product-tile__outer')]
//div[contains(@class, 'product-tile__name')]//a
//form[contains(@class, 'js-add-to-cart')]/@data-price
//input[@name='product_id']/@value
```

---

## Универсальные селекторы для обоих сайтов

### Для получения всех товаров
```python
# TechProm
products = response.css('.products-list.card .product-wrap')

# DiCENTRE
products = response.css('.product-list .product-tile__outer')
```

---

## Примечания

1. **TechProm** использует Bitrix-разметку с ID вида `bx_...`.
2. **DiCENTRE** использует WebAsyst-разметку с карточками `product-tile`.
3. Оба сайта могут подгружать часть данных асинхронно, поэтому при изменениях верстки может понадобиться Selenium/Playwright.
4. Цены содержат пробелы, `&nbsp;`, HTML-теги и символ рубля, поэтому перед сохранением нужна очистка до числа.
5. Изображения могут использовать lazy-load (`data-src`, `data-img`) — это важно, если позже в модели товара появится поле изображения.
