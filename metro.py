from playwright.sync_api import sync_playwright
import csv
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

        # Save to CSV
        keys = all_data[0].keys() if all_data else []
        with open("metro_flyer_data.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_data)

        print(f"\n✅ Done! {len(all_data)} products saved to metro_flyer_data.csv.")
        browser.close()

if __name__ == "__main__":
    scrape_metro_flyer()
