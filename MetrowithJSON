from playwright.sync_api import sync_playwright
import csv
import json
import time

def extract_product_data(product, base_url):
    try:
        name = product.get_attribute('data-product-name') or ''
        brand = product.get_attribute('data-product-brand') or ''
        category = product.get_attribute('data-product-category') or ''
        image = product.query_selector('picture img')
        image_url = image.get_attribute('src') if image else ''
        
        link_tag = product.query_selector('a.product-details-link')
        product_url = base_url + link_tag.get_attribute('href') if link_tag else ''
        
        unit_details = product.query_selector('.head__unit-details')
        unit = unit_details.inner_text().strip() if unit_details else ''

        reg_price_elem = product.query_selector('.pricing__before-price span')
        reg_price = reg_price_elem.inner_text().strip() if reg_price_elem else ''

        sale_price_elem = product.query_selector('.pi-price-promo')
        sale_price = sale_price_elem.inner_text().strip() if sale_price_elem else ''

        per_unit_elem = product.query_selector('.pricing__secondary-price')
        per_unit = per_unit_elem.inner_text().strip() if per_unit_elem else ''

        return {
            'name': name,
            'brand': brand,
            'unit': unit,
            'regular_price': reg_price,
            'sale_price': sale_price,
            'price_per_unit': per_unit,
            'image_url': image_url,
            'product_url': product_url,
            'category': category
        }
    except Exception as e:
        print("Error extracting product:", e)
        return {}

def save_as_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_as_html(data, filename):
    html = """
    <html>
    <head>
        <title>Metro Flyer Preview</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px; }
            h1 { color: #444; }
            .product { border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #fff; margin-bottom: 10px; display: flex; gap: 15px; }
            .product img { max-width: 100px; height: auto; border-radius: 4px; }
            .details { flex: 1; }
            .price { color: #d81e05; font-weight: bold; }
            .regular { text-decoration: line-through; color: #777; }
            .unit, .category { font-size: 0.9em; color: #555; }
        </style>
    </head>
    <body>
        <h1>Metro Flyer - Product Preview</h1>
    """

    for item in data:
        html += f"""
        <div class="product">
            <img src="{item['image_url']}" alt="{item['name']}">
            <div class="details">
                <h3>{item['brand']} - {item['name']}</h3>
                <p class="unit">{item['unit']}</p>
                <p class="category">Category: {item['category']}</p>
                <p>
                    <span class="price">{item['sale_price']}</span> 
                    <span class="regular">{item['regular_price']}</span> 
                    <span class="unit">({item['price_per_unit']})</span>
                </p>
                <a href="{item['product_url']}" target="_blank">View Product</a>
            </div>
        </div>
        """

    html += "</body></html>"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

def scrape_metro_flyer():
    base_url = "https://www.metro.ca"
    flyer_url = base_url + "/en/online-grocery/flyer"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(flyer_url)
        time.sleep(2)
        
        # Get total number of pages
        pagination = page.query_selector_all('.ppn--element')
        last_page = 1
        for item in pagination:
            href = item.get_attribute('href')
            if href and 'flyer-page-' in href:
                try:
                    num = int(href.split('flyer-page-')[1].split('?')[0])
                    last_page = max(last_page, num)
                except:
                    continue

        print(f"Found {last_page} pages.")

        all_data = []
        for page_num in range(1, last_page + 1):
            if page_num == 1:
                url = flyer_url
            else:
                url = f"{base_url}/en/online-grocery/flyer-page-{page_num}?sortOrder=relevance&filter=%3Arelevance%3Adeal%3AFlyer+%26+Deals"

            print(f"Scraping Page {page_num}: {url}")
            page.goto(url, timeout=60000)
            time.sleep(2)

            products = page.query_selector_all('.tile-product')
            print(f"Found {len(products)} products on page {page_num}")

            for product in products:
                data = extract_product_data(product, base_url)
                data["page"] = page_num
                if data:
                    all_data.append(data)

        # Save CSV
        keys = all_data[0].keys() if all_data else []
        with open("metro_flyer_data.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_data)

        # Save JSON and HTML preview
        save_as_json(all_data, "metro_flyer_data.json")
        save_as_html(all_data, "metro_flyer_preview.html")

        print(f"\n✅ Done! Saved {len(all_data)} products to:")
        print("• metro_flyer_data.csv")
        print("• metro_flyer_data.json")
        print("• metro_flyer_preview.html")

        browser.close()

if __name__ == "__main__":
    scrape_metro_flyer()
