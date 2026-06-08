# CSS Selectors для парсеров смартфонов

## 1. TECHPROM (Смартфоны.html)

### Структура сайта: Bitrix24 (магнит-шаблон)

#### Контейнер продуктов:
```
.products-list.card
```

#### Каждый товар (wrapper):
```
.product-wrap
```

#### Элементы товара:
- **Название товара:**
  ```
  .product-card a.name
  ```
  или более специфично:
  ```
  .product-wrap a.name
  ```

- **Цена:**
  ```
  .price span[id*="_price"]
  ```
  или:
  ```
  .price-container .price span
  ```

- **Изображение:**
  ```
  .img-product-link img
  ```

- **Ссылка на товар:**
  ```
  .product-wrap a.name
  ```
  атрибут: `href`

- **ID товара:** (в атрибуте родительского div)
  ```
  .product-wrap div[id*="bx_"]
  ```
  атрибут: `id` (содержит ID товара)

- **Статус наличия:**
  ```
  .stock .product-item-quantity
  ```

#### XPath альтернативы:
```xpath
//div[@class='product-wrap']
//a[@class='name']
//span[contains(@id, '_price')]
//img[@class='img-product-link']
```

---

## 2. DiCENTRE (Смартфоны и телефоны... DiCENTRE.html)

### Структура сайта: WebAsyst (МастерШоп)

#### Контейнер продуктов:
```
.products-grid
или
div[class*="products"]
```

#### Каждый товар (wrapper):
```
.product-card
```

#### Элементы товара:
- **Название товара:**
  ```
  .product-card__name
  или
  .product-card a.product-card__name
  ```

- **Цена:**
  ```
  .product-card__price
  или
  .product-card__price-current
  ```

- **Изображение:**
  ```
  .product-card__image
  или
  .product-card img
  ```

- **Ссылка на товар:**
  ```
  .product-card a[href*="/sotovye-telefony/"]
  ```

- **Рейтинг/Отзывы:**
  ```
  .product-card__rating
  или
  .product-card__reviews-count
  ```

- **ID товара:** (в атрибуте data)
  ```
  .product-card[data-id]
  атрибут: data-id
  ```

#### XPath альтернативы:
```xpath
//div[@class='product-card']
//a[@class='product-card__name']
//span[@class='product-card__price']
//img[@class='product-card__image']
```

---

## Универсальные селекторы для обоих сайтов

### Для получения всех товаров:
```python
# TechProm
products = response.css('.products-list.card .product-wrap')

# DiCENTRE
products = response.css('.product-card')
```

---

## Примечания:

1. **TechProm** использует шаблон Bitrix24, CSS классы заканчиваются на `bx_`
2. **DiCENTRE** использует платформу WebAsyst, более структурированные BEM-селекторы
3. Оба сайта поддерживают асинхронную загрузку, может потребоваться Selenium/Playwright для некоторых страниц
4. Цены обычно содержат не-разрывные пробелы (`&nbsp;`), требуется очистка
5. Изображения часто загружаются через data-lazy, может потребоваться обработка атрибутов `data-src`
