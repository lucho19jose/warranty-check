import requests
import json
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

def convert_date_to_ddmmyyyy(date_string):
    """Convert date from 'Month DD, YYYY' format to 'DD/MM/YYYY' format"""
    if not date_string:
        return None
    
    try:
        date_obj = datetime.strptime(date_string.replace(',', ''), "%B %d %Y")
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        try:
            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                date_obj = datetime.strptime(date_string, fmt)
                return date_obj.strftime("%d/%m/%Y")
        except ValueError:
            return date_string

def get_ultra_fast_chrome_options():
    """Get Chrome options optimized for Ubuntu server compatibility"""
    options = Options()
    
    # Essential Ubuntu server compatibility flags
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-gpu-sandbox")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--remote-debugging-port=9222")
    
    # Critical for Ubuntu server - specify user data directory
    options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    options.add_argument("--data-path=/tmp/chrome-data")
    options.add_argument("--disk-cache-dir=/tmp/chrome-cache")
    
    # Single process mode for better compatibility
    options.add_argument("--single-process")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    
    # Display settings
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Performance optimizations (keep JS and CSS enabled for HP site)
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-default-apps")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    # Logging
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Content preferences
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.media_stream": 2,
        "profile.default_content_setting_values.geolocation": 2,
        "profile.default_content_setting_values.plugins": 2,
        "profile.default_content_settings.popups": 2,
    }
    options.add_experimental_option("prefs", prefs)
    
    return options

def extract_warranty_ultra_fast(serial_number):
    """Ultra-fast warranty extraction with optimized Chrome"""
    
    options = get_ultra_fast_chrome_options()
    driver = None
    try:
        # Create temp directories for Chrome
        import os
        os.makedirs('/tmp/chrome-user-data', exist_ok=True)
        os.makedirs('/tmp/chrome-data', exist_ok=True)
        os.makedirs('/tmp/chrome-cache', exist_ok=True)
        
        start_time = time.time()
        
        # Optimized driver initialization
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(1)
        
        print(f"⚡ Browser started in {time.time() - start_time:.2f}s", file=sys.stderr)
        
        # Navigate with minimal wait
        nav_start = time.time()
        driver.get("https://support.hp.com/us-en/check-warranty")
        print(f"⚡ Page loaded in {time.time() - nav_start:.2f}s", file=sys.stderr)
        # time.sleep(5) # Remove or reduce delay for headless mode
        
        # Ultra-quick cookie handling (no wait, fire and forget)
        try:
            driver.execute_script("""
                var button = document.getElementById('onetrust-accept-btn-handler');
                if (button) button.click();
            """)
        except:
            pass
        
        # Immediate form interaction
        input_start = time.time()
        
        # Use JavaScript for faster form filling
        driver.execute_script(f"""
            var input = document.getElementById('inputtextpfinder');
            if (input) {{
                input.value = '{serial_number}';
                input.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}
        """)
        
        # Immediate submit via JavaScript
        driver.execute_script("""
            var submitBtn = document.getElementById('FindMyProduct');
            if (submitBtn) submitBtn.click();
        """)
        # time.sleep(5) # Remove or reduce delay for headless mode
        
        print(f"⚡ Form submitted in {time.time() - input_start:.2f}s", file=sys.stderr)
        
        # Aggressive results waiting with shorter timeout
        result_start = time.time()
        try:
            # Reduce wait time and check more frequently
            WebDriverWait(driver, 30, poll_frequency=0.5).until( # Increased timeout for results
                EC.url_contains("warrantyresult")
            )
            print(f"⚡ Results loaded in {time.time() - result_start:.2f}s", file=sys.stderr)
            # time.sleep(1) # Remove or reduce delay for headless mode
        except TimeoutException:
            if driver:
                driver.quit()
            return {"error": "Results page timeout - CAPTCHA may be required or page structure changed"}
        
        # Ultra-fast data extraction with JavaScript
        extract_start = time.time()
        result = {
            "Brand": "HP",  # Default since we know it's HP
            "Product Name": None,
            "Serial Number": serial_number,
            "Warranty Start": None,
            "Warranty End": None
        }
        
        # Use JavaScript to find product name faster
        try:
            product_name = driver.execute_script("""
                var selectors = ['h1', 'h2', '.product-title', '[data-testid="product-name"]'];
                for (var i = 0; i < selectors.length; i++) {
                    var elements = document.querySelectorAll(selectors[i]);
                    for (var j = 0; j < Math.min(elements.length, 3); j++) {
                        var text = elements[j].textContent.trim();
                        if (text && text.length > 5 && (text.includ
                        es('HP') || text.includes('Compaq'))) {
                            return text;
                        }
                    }
                }
                return null;
            """)
            if product_name:
                result["Product Name"] = product_name
        except:
            pass
        
        # Ultra-fast warranty date extraction with JavaScript
        try:
            warranty_dates = driver.execute_script("""
                var result = {start: null, end: null};
                
                // Method 1: Look for warranty info structure
                var startLabel = document.querySelector('div.label:contains("Start date"), div:contains("Start date")');
                var endLabel = document.querySelector('div.label:contains("End date"), div:contains("End date")');
                
                if (startLabel) {
                    var startText = startLabel.nextElementSibling;
                    if (startText) result.start = startText.textContent.trim();
                }
                
                if (endLabel) {
                    var endText = endLabel.nextElementSibling;
                    if (endText) result.end = endText.textContent.trim();
                }
                
                // Method 2: Search all text for date patterns if not found
                if (!result.start || !result.end) {
                    var allText = document.body.textContent;
                    var datePattern = /([A-Za-z]+ \\d{1,2}, \\d{4})/g;
                    var dates = allText.match(datePattern);
                    
                    if (dates && dates.length >= 2) {
                        if (!result.start) result.start = dates[0];
                        if (!result.end) result.end = dates[1];
                    }
                }
                
                return result;
            """)
            
            if warranty_dates['start']:
                result["Warranty Start"] = convert_date_to_ddmmyyyy(warranty_dates['start'])
            if warranty_dates['end']:
                result["Warranty End"] = convert_date_to_ddmmyyyy(warranty_dates['end'])
                
        except Exception as e:
            # Fallback to Selenium if JavaScript fails
            try:
                start_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'info-item')]//div[contains(@class, 'label') and normalize-space(text())='Start date']")
                if start_elements:
                    start_date_element = start_elements[0].find_element(By.XPATH, "./following-sibling::div[contains(@class, 'text')]")
                    result["Warranty Start"] = convert_date_to_ddmmyyyy(start_date_element.text.strip())
                
                end_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'info-item')]//div[contains(@class, 'label') and normalize-space(text())='End date']")
                if end_elements:
                    end_date_element = end_elements[0].find_element(By.XPATH, "./following-sibling::div[contains(@class, 'text')]")
                    result["Warranty End"] = convert_date_to ddmmyyyy(end_date_element.text.strip())
            except:
                pass
        
        print(f"⚡ Data extracted in {time.time() - extract_start:.2f}s", file=sys.stderr)
        print(f"⚡ Total time: {time.time() - start_time:.2f}s", file=sys.stderr)
        
        if driver:
            driver.quit()
        return result
        
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass # Ignore errors during quit if already failed
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