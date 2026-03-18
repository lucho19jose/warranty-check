import requests
import json
import sys
import time
import re
import os
import threading
from datetime import datetime


def convert_date_to_ddmmyyyy(date_string):
    """Convert date from various formats to 'DD/MM/YYYY' format"""
    if not date_string:
        return None

    for fmt in ["%B %d, %Y", "%B %d %Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            date_obj = datetime.strptime(date_string.replace(',', '').strip(), fmt.replace(',', ''))
            return date_obj.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return date_string


def get_hp_product_info(serial_number):
    """Get HP product info via API (fast, no browser needed)"""
    try:
        r = requests.get(
            "https://support.hp.com/wcc-services/search/sn/us-en",
            params={"context": "contact", "serialNumber": serial_number, "productNumber": ""},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                "Accept": "application/json",
            },
            timeout=10,
        )
        data = r.json()
        if data.get("code") == 200 and data.get("data"):
            return data["data"]
    except Exception as e:
        print(f"[HP] Product API error: {e}", file=sys.stderr)
    return None


# --- Persistent browser pool ---
_browser_lock = threading.Lock()
_browser_driver = None
_browser_last_used = 0


def _create_chrome_driver():
    """Create a new headless Chrome driver"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])

    os.makedirs('/tmp/chrome-user-data', exist_ok=True)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(20)
    driver.implicitly_wait(2)
    return driver


def _get_browser():
    """Get the persistent browser, creating one if needed"""
    global _browser_driver, _browser_last_used

    # Check if existing driver is still alive
    if _browser_driver is not None:
        try:
            _browser_driver.title  # quick health check
            return _browser_driver, False
        except Exception:
            print("[HP] Stale browser detected, creating new one", file=sys.stderr)
            try:
                _browser_driver.quit()
            except Exception:
                pass
            _browser_driver = None

    # Create new driver
    _browser_driver = _create_chrome_driver()
    _browser_last_used = time.time()
    return _browser_driver, True


def _release_browser(force_quit=False):
    """Release browser back to pool, or quit if force_quit"""
    global _browser_driver, _browser_last_used
    if force_quit and _browser_driver is not None:
        try:
            _browser_driver.quit()
        except Exception:
            pass
        _browser_driver = None
    else:
        _browser_last_used = time.time()


def extract_warranty_ultra_fast(serial_number):
    """HP warranty lookup: get product info via API, then reusable browser for dates"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    start_time = time.time()

    # Step 1: Get product info via API (fast, ~0.5s)
    product_info = get_hp_product_info(serial_number)
    product_name = None
    direct_url = None

    if product_info:
        product_name = product_info.get("productName")
        seo_name = product_info.get("SEOFriendlyName", "")
        series_oid = product_info.get("productSeriesOID", "")
        model_oid = product_info.get("productNameOID", "")
        sku = product_info.get("productNumber", "")
        direct_url = f"https://support.hp.com/us-en/warrantyresult/{seo_name}/{series_oid}/model/{model_oid}?sku={sku}&serialnumber={serial_number}"
        print(f"[HP] Product info in {time.time() - start_time:.2f}s: {product_name}", file=sys.stderr)

    # Step 2: Get warranty dates using persistent browser
    with _browser_lock:
        driver = None
        try:
            driver, is_new = _get_browser()
            if is_new:
                print(f"[HP] New browser started in {time.time() - start_time:.2f}s", file=sys.stderr)
            else:
                print(f"[HP] Reusing browser ({time.time() - start_time:.2f}s)", file=sys.stderr)

            # Navigate directly to result page if we have product info
            if direct_url:
                driver.get(direct_url)
            else:
                driver.get("https://support.hp.com/us-en/check-warranty")

                # Accept cookies
                try:
                    time.sleep(1)
                    driver.execute_script("var b=document.getElementById('onetrust-accept-btn-handler');if(b)b.click();")
                except Exception:
                    pass

                # Fill and submit form
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "inputtextpfinder")))
                driver.execute_script(f"""
                    var input = document.getElementById('inputtextpfinder');
                    if (input) {{ input.value = '{serial_number}'; input.dispatchEvent(new Event('input', {{bubbles: true}})); }}
                """)
                time.sleep(0.5)
                driver.execute_script("var btn=document.getElementById('FindMyProduct');if(btn)btn.click();")

            # Wait for warranty content to appear
            print(f"[HP] Waiting for warranty data...", file=sys.stderr)
            WebDriverWait(driver, 15).until(
                lambda d: "Start date" in d.page_source or "End date" in d.page_source or "Expired" in d.page_source
            )
            time.sleep(1)

            print(f"[HP] Page ready in {time.time() - start_time:.2f}s", file=sys.stderr)

            # Extract warranty dates
            warranty_info = driver.execute_script("""
                function cleanDateAfterLabel(text, label) {
                    var idx = text.indexOf(label);
                    if (idx === -1) return null;
                    var after = text.substring(idx + label.length);
                    var m = after.match(/(January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},?\\s+\\d{4}/);
                    return m ? m[0] : null;
                }
                var allText = document.body.textContent;
                var result = {start: null, end: null, product: null};
                result.start = cleanDateAfterLabel(allText, 'Start date');
                result.end = cleanDateAfterLabel(allText, 'End date');

                var headings = document.querySelectorAll('h1, h2, .product-title');
                for (var i = 0; i < headings.length; i++) {
                    var text = headings[i].textContent.trim();
                    if (text && text.length > 5 && (text.includes('HP') || text.includes('Compaq'))) {
                        result.product = text;
                        break;
                    }
                }
                return result;
            """)

            result = {
                "brand": "HP",
                "product_name": product_name or warranty_info.get('product'),
                "serial_number": serial_number,
                "warranty_start": convert_date_to_ddmmyyyy(warranty_info.get('start')),
                "warranty_end": convert_date_to_ddmmyyyy(warranty_info.get('end')),
            }

            total = time.time() - start_time
            print(f"[HP] Done in {total:.2f}s", file=sys.stderr)
            _release_browser()
            return result

        except Exception as e:
            print(f"[HP] Error: {e}", file=sys.stderr)
            # Kill broken browser so next request gets a fresh one
            _release_browser(force_quit=True)
            return {"error": str(e)}


def main():
    if len(sys.argv) > 1:
        serial = sys.argv[1].upper()
    else:
        serial = input("Serial: ").strip().upper()

    if not serial:
        print('{"error": "No serial number provided"}')
        return

    result = extract_warranty_ultra_fast(serial)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
