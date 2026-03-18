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
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

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
    """Get Chrome options optimized for maximum speed and Ubuntu server compatibility"""
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
    
    # Performance optimizations
    options.add_argument("--single-process")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    
    # Ubuntu server directory fixes
    options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    options.add_argument("--data-path=/tmp/chrome-data")
    options.add_argument("--disk-cache-dir=/tmp/chrome-cache")
    
    # Essential display settings
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # Disable unnecessary features for speed (but keep JS and CSS!)
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
        # Create temp directories
        import os
        os.makedirs('/tmp/chrome-user-data', exist_ok=True)
        os.makedirs('/tmp/chrome-data', exist_ok=True)
        os.makedirs('/tmp/chrome-cache', exist_ok=True)
        
        start_time = time.time()
        
        # Initialize driver
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(20)
            driver.implicitly_wait(3)
            print(f"⚡ Browser started in {time.time() - start_time:.2f}s", file=sys.stderr)
        except Exception as driver_error:
            print(f"❌ Driver failed: {driver_error}", file=sys.stderr)
            return {"error": f"Chrome driver failed: {str(driver_error)}"}
        
        # Navigate to HP warranty page
        nav_start = time.time()
        try:
            driver.get("https://support.hp.com/us-en/check-warranty")
            print(f"⚡ Page loaded in {time.time() - nav_start:.2f}s", file=sys.stderr)
        except Exception as nav_error:
            if driver:
                driver.quit()
            return {"error": f"Page navigation failed: {str(nav_error)}"}
        
        # Handle cookies
        try:
            time.sleep(2)
            driver.execute_script("""
                var cookieButton = document.getElementById('onetrust-accept-btn-handler') || 
                                  document.querySelector('[id*="accept"]') ||
                                  document.querySelector('[class*="accept"]');
                if (cookieButton) cookieButton.click();
            """)
            time.sleep(1)
        except:
            pass
        
        # Form submission with multiple attempts
        input_start = time.time()
        success = False
        
        for attempt in range(3):
            try:
                print(f"🔄 Attempt {attempt + 1} to submit form...", file=sys.stderr)
                
                # Wait for input field
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "inputtextpfinder"))
                )
                
                # Clear and input serial number
                input_field = driver.find_element(By.ID, "inputtextpfinder")
                input_field.clear()
                input_field.send_keys(serial_number)
                time.sleep(0.5)
                
                # Try different submit methods
                submit_selectors = ["FindMyProduct", "[type='submit']", "button[class*='submit']"]
                button_clicked = False
                
                for selector in submit_selectors:
                    try:
                        if selector.startswith('[') or selector.startswith('button'):
                            element = driver.find_element(By.CSS_SELECTOR, selector)
                        else:
                            element = driver.find_element(By.ID, selector)
                        
                        if element.is_enabled() and element.is_displayed():
                            driver.execute_script("arguments[0].click();", element)
                            button_clicked = True
                            print(f"✅ Clicked button: {selector}", file=sys.stderr)
                            break
                    except:
                        continue
                
                if not button_clicked:
                    input_field.send_keys("\n")
                    print("✅ Pressed Enter", file=sys.stderr)
                
                # Wait for page change
                time.sleep(3)
                current_url = driver.current_url
                page_source = driver.page_source
                
                if ("warrantyresult" in current_url or 
                    "warranty" in page_source.lower() and "start date" in page_source.lower() or
                    current_url != "https://support.hp.com/us-en/check-warranty"):
                    success = True
                    print(f"⚡ Form submitted successfully", file=sys.stderr)
                    break
                else:
                    print(f"⚠️ Still on search page, attempt {attempt + 1}", file=sys.stderr)
                    time.sleep(2)
                    
            except Exception as form_error:
                print(f"⚠️ Form attempt {attempt + 1} failed: {form_error}", file=sys.stderr)
                time.sleep(2)
        
        if not success:
            print("❌ All form submission attempts failed", file=sys.stderr)
            page_text = driver.page_source.lower()
            if any(keyword in page_text for keyword in ['captcha', 'robot', 'verify', 'security']):
                return {"error": "CAPTCHA or security verification required"}
            return {"error": "Form submission failed"}
        
        # Wait for results
        result_start = time.time()
        for wait_attempt in range(3):
            try:
                print(f"🔄 Wait attempt {wait_attempt + 1} for results...", file=sys.stderr)
                
                # Multiple wait strategies
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: "warrantyresult" in d.current_url or d.current_url != "https://support.hp.com/us-en/check-warranty"
                    )
                    break
                except TimeoutException:
                    try:
                        WebDriverWait(driver, 5).until(
                            lambda d: any(keyword in d.page_source.lower() for keyword in ['start date', 'end date', 'warranty status'])
                        )
                        break
                    except TimeoutException:
                        time.sleep(2)
                        
            except Exception as wait_error:
                print(f"⚠️ Wait error: {wait_error}", file=sys.stderr)
                time.sleep(2)
        
        print(f"🔍 Final URL: {driver.current_url}", file=sys.stderr)
        
        # Data extraction
        result = {
            "brand": "HP",
            "product_name": None,
            "serial_number": serial_number,
            "warranty_start": None,
            "warranty_end": None
        }
        
        try:
            page_text = driver.page_source
            
            # Check for error messages
            if any(error in page_text.lower() for error in ['not found', 'invalid serial', 'unable to find']):
                return {"error": f"HP could not find warranty information for serial number {serial_number}"}
            
            # Extract product name using regex
            import re
            product_patterns = [
                r'HP\s+[^<>\n]{10,100}',
                r'Compaq\s+[^<>\n]{10,100}',
            ]
            
            for pattern in product_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    result["product_name"] = matches[0].strip()
                    break
            
            # Extract warranty dates
            date_patterns = [
                r'(?:Start\s*date|Coverage\s*start)[:\s]*([A-Za-z]+ \d{1,2}, \d{4})',
                r'(?:End\s*date|Coverage\s*end)[:\s]*([A-Za-z]+ \d{1,2}, \d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}-\d{2}-\d{2})'
            ]
            
            all_dates = []
            for pattern in date_patterns:
                dates = re.findall(pattern, page_text, re.IGNORECASE)
                all_dates.extend(dates)
            
            if len(all_dates) >= 2:
                result["warranty_start"] = convert_date_to_ddmmyyyy(all_dates[0])
                result["warranty_end"] = convert_date_to_ddmmyyyy(all_dates[1])
            elif len(all_dates) == 1:
                result["warranty_end"] = convert_date_to_ddmmyyyy(all_dates[0])
            
            # JavaScript extraction fallback
            if not result["product_name"] or not result["warranty_start"]:
                try:
                    js_result = driver.execute_script("""
                        var text = document.body.textContent;
                        var result = {};
                        
                        var productMatch = text.match(/HP\\s+[\\w\\s-]{10,100}/i) || text.match(/Compaq\\s+[\\w\\s-]{10,100}/i);
                        if (productMatch) result.product = productMatch[0].trim();
                        
                        var dateMatches = text.match(/[A-Za-z]+ \\d{1,2}, \\d{4}/g);
                        if (dateMatches && dateMatches.length >= 2) {
                            result.start = dateMatches[0];
                            result.end = dateMatches[dateMatches.length - 1];
                        }
                        
                        return result;
                    """)
                    
                    if js_result.get('product'):
                        result["product_name"] = js_result['product']
                    if js_result.get('start'):
                        result["warranty_start"] = convert_date_to_ddmmyyyy(js_result['start'])
                    if js_result.get('end'):
                        result["warranty_end"] = convert_date_to_ddmmyyyy(js_result['end'])
                        
                except Exception as js_error:
                    print(f"⚠️ JavaScript extraction error: {js_error}", file=sys.stderr)
            
            print(f"⚡ Data extraction completed in {time.time() - result_start:.2f}s", file=sys.stderr)
            print(f"⚡ Total time: {time.time() - start_time:.2f}s", file=sys.stderr)
            
        except Exception as extract_error:
            print(f"⚠️ Extraction error: {extract_error}", file=sys.stderr)
        
        # Save debug info if no data found
        if not any([result["product_name"], result["warranty_start"], result["warranty_end"]]):
            try:
                with open("/tmp/hp_debug.html", "w") as f:
                    f.write(driver.page_source)
                print("💾 Debug HTML saved to /tmp/hp_debug.html", file=sys.stderr)
            except:
                pass
        
        driver.quit()
        return result
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if driver:
            try:
                driver.quit()
            except:
                pass
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