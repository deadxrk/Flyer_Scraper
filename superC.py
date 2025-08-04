from playwright.sync_api import sync_playwright
import time
import csv
import json
from datetime import datetime

BASE_URL = "https://www.superc.ca/en/online-grocery/flyer"
PAGE_URL_TEMPLATE = "https://www.superc.ca/en/online-grocery/flyer-page-{page}?sortOrder=relevance&filter=%3Arelevance%3Adeal%3AFlyer+%26+Deals"

def extract_products_from_page(page, page_num):
    print(f"🔍 Extracting products on page {page_num}...")
    products = page.query_selector_all('.default-product-tile.tile-product.item-addToCart.tile-product--effective-date')
    page_data = []

    for i, product in enumerate(products, 1):
        try:
            product_name = product.get_attribute('data-product-name') or "N/A"
            brand_elem = product.query_selector('.head__brand')
            brand = brand_elem.inner_text().strip() if brand_elem else "N/A"
            title_elem = product.query_selector('.head__title')
            title = title_elem.inner_text().strip() if title_elem else product_name
            unit_elem = product.query_selector('.head__unit-details')
            unit_details = unit_elem.inner_text().strip() if unit_elem else "N/A"
            sale_price_elem = product.query_selector('.pricing__sale-price .price-update')
            sale_price = sale_price_elem.inner_text().strip() if sale_price_elem else "N/A"
            regular_price_elem = product.query_selector('.pricing__before-price span')
            regular_price = regular_price_elem.inner_text().strip() if regular_price_elem else "N/A"
            unit_price_elem = product.query_selector('.pricing__secondary-price span')
            unit_price = unit_price_elem.inner_text().strip() if unit_price_elem else "N/A"
            valid_until_elem = product.query_selector('.pricing__until-date span')
            valid_until = valid_until_elem.inner_text().strip() if valid_until_elem else "N/A"
            category = product.get_attribute('data-product-category') or "N/A"
            product_code = product.get_attribute('data-product-code') or "N/A"
            img_elem = product.query_selector('img')
            image_url = img_elem.get_attribute('src') if img_elem else "N/A"
            image_alt = img_elem.get_attribute('alt') if img_elem else "N/A"
            link_elem = product.query_selector('.product-details-link')
            product_url = link_elem.get_attribute('href') if link_elem else "N/A"
            if product_url and not product_url.startswith('http'):
                product_url = "https://www.superc.ca" + product_url
            has_sale = product.query_selector('.icon--sale') is not None
            is_quebec = product.query_selector('.icon--quebec') is not None

            page_data.append({
                'page': page_num,
                'product_code': product_code,
                'brand': brand,
                'product_name': product_name,
                'title': title,
                'unit_details': unit_details,
                'sale_price': sale_price,
                'regular_price': regular_price,
                'unit_price': unit_price,
                'category': category,
                'valid_until': valid_until,
                'has_sale': has_sale,
                'is_quebec_product': is_quebec,
                'image_url': image_url,
                'image_alt': image_alt,
                'product_url': product_url,
                'scraped_at': datetime.now().isoformat()
            })

            if i % 50 == 0 or i <= 10:
                print(f"   ✅ Product {i}: {brand} - {title} - {sale_price}")
            elif i == 11:
                print("   ... (showing every 50th product) ...")

        except Exception as e:
            print(f"❌ Error on product {i}: {e}")
            page_data.append({
                'page': page_num,
                'error': str(e),
                'scraped_at': datetime.now().isoformat()
            })

    print(f"✅ Extracted {len(page_data)} products from page {page_num}")
    return page_data

def scrape_superc_all_pages():
    print("🚀 Starting full SuperC flyer scrape (direct URL pagination)...")
    all_data = []
    total_pages = 35  # You can update this dynamically later

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            for page_num in range(1, total_pages + 1):
                if page_num == 1:
                    url = BASE_URL
                else:
                    url = PAGE_URL_TEMPLATE.format(page=page_num)

                print(f"\n📄 Processing page {page_num} → {url}")
                page.goto(url, timeout=60000)

                # Dismiss cookies only on page 1
                if page_num == 1:
                    try:
                        page.locator('button:has-text("Refuse all")').click(timeout=3000)
                        print("✅ Refused cookies")
                    except:
                        print("ℹ️ No cookie popup")

                page.wait_for_selector('.grid--container.products-second-block', timeout=30000)
                time.sleep(1)
                page_data = extract_products_from_page(page, page_num)
                all_data.extend(page_data)

            browser.close()

            # Save
            success_data = [p for p in all_data if 'error' not in p]
            csv_file = 'superc_products_all_pages.csv'
            json_file = 'superc_products_all_pages.json'

            if success_data:
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=success_data[0].keys())
                    writer.writeheader()
                    writer.writerows(success_data)

                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, indent=2, ensure_ascii=False)

                print(f"\n💾 Saved {len(success_data)} products to:")
                print(f"   📄 {csv_file}")
                print(f"   📄 {json_file}")

            return all_data

    except Exception as e:
        print(f"\n❌ Scraper crashed: {e}")
        return []

if __name__ == "__main__":
    results = scrape_superc_all_pages()
    if results:
        scraped = [p for p in results if 'error' not in p]
        print(f"\n🎉 Done! Scraped {len(scraped)} products in total.")
    else:
        print("😞 No data collected.")
