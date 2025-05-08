import requests
import sys # Import sys to access command-line arguments
# Remove Selenium and related imports
# from bs4 import BeautifulSoup # Not strictly needed if only parsing JS
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException
# import time # Import time for potential waits
import re # Import regular expressions
import json # Import JSON parser

def get_lenovo_warranty_info(serial_number):
    """
    Fetches warranty information for a given Lenovo serial number using:
    1. API call to get product ID and Model.
    2. Fetch warranty page HTML and parse embedded JavaScript variable (ds_warranties).

    Args:
        serial_number (str): The serial number of the Lenovo device.

    Returns:
        dict: A dictionary containing model, start_date, and end_date,
              or None if information cannot be retrieved or parsed.
    """
    product_api_url = f"https://pcsupport.lenovo.com/us/en/api/v4/mse/getproducts?productId={serial_number}"
    model = 'N/A'
    start_date = 'N/A'
    end_date = 'N/A'
    product_id_path = None
    response_api = None # Initialize
    response_html = None # Initialize

    # Use more comprehensive headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'application/json, text/javascript, */*; q=0.01', # Adjusted for API
    }
    html_headers = headers.copy()
    html_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' # For HTML page


    # --- Step 1: Call API to get Product ID and Model ---
    try:
        print(f"Calling API: {product_api_url}")
        response_api = requests.get(product_api_url, headers=headers, timeout=15)
        response_api.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response_api.json()

        if isinstance(data, list) and len(data) > 0:
            product_info = data[0]
            model = product_info.get('Name', 'N/A')
            product_id_full = product_info.get('Id')
            if product_id_full:
                 product_id_path = product_id_full.lower()
                 print(f"Product ID path from API: {product_id_path}")
            else:
                print("Could not find 'Id' in API response.")
                return None
        else:
            print(f"Product not found or unexpected JSON structure from product API: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during product API request to {product_api_url}: {e}")
        if response_api is not None:
            print(f"API Status Code: {response_api.status_code}")
            print(f"API Response Text: {response_api.text[:500]}...")
        return None
    except ValueError as e: # Catches JSON decoding errors
        print(f"Error decoding product API JSON response: {e}")
        if response_api is not None:
            print(f"API Response Text: {response_api.text[:500]}...")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        return None

    # --- Step 2: Fetch Warranty Page HTML and Parse Embedded JS ---
    if product_id_path:
        warranty_page_url = f"https://pcsupport.lenovo.com/us/en/products/{product_id_path}/warranty"
        # Changed print statement
        print(f"Fetching warranty page HTML with requests: {warranty_page_url}")

        try:
            # Fetch HTML using requests
            response_html = requests.get(warranty_page_url, headers=html_headers, timeout=20)
            response_html.raise_for_status()
            html_content = response_html.text

            # Regex to find the ds_warranties JavaScript variable assignment
            warranty_match = re.search(r'var ds_warranties\s*=\s*window\.ds_warranties\s*\|\|\s*({.*?});', html_content, re.DOTALL)

            if warranty_match:
                json_str = warranty_match.group(1)
                try:
                    warranty_info = json.loads(json_str)

                    # Extract data from the parsed JSON structure
                    base_warranties = warranty_info.get('BaseWarranties', [])
                    if base_warranties and isinstance(base_warranties, list) and len(base_warranties) > 0:
                        start_date = base_warranties[0].get('Start', 'Not Found in JSON')
                        end_date = base_warranties[0].get('End', 'Not Found in JSON')
                        print("Successfully parsed dates from ds_warranties.")
                    else:
                         print("Could not find 'BaseWarranties' array or it was empty in ds_warranties.")
                         start_date = 'BaseWarranties Not Found'
                         end_date = 'BaseWarranties Not Found'

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from ds_warranties variable: {e}")
                    print(f"Extracted string part: {json_str[:500]}...")
                    start_date = 'JSON Parse Error'
                    end_date = 'JSON Parse Error'
                except Exception as e:
                    print(f"Error processing parsed ds_warranties data: {e}")
                    start_date = 'Data Processing Error'
                    end_date = 'Data Processing Error'
            else:
                print("Could not find the 'ds_warranties' JavaScript variable in the HTML source.")
                # Optional: Add checks for other text to see if the page loaded correctly at all
                if "Warranty service" not in html_content and "Base Warranty" not in html_content:
                     print("Warning: Key warranty text markers also missing from the page source, page might not have loaded correctly.")
                start_date = 'JS Variable Not Found'
                end_date = 'JS Variable Not Found'

        except requests.exceptions.RequestException as e:
            print(f"Error during warranty page request to {warranty_page_url}: {e}")
            if response_html is not None:
                print(f"HTML Status Code: {response_html.status_code}")
            start_date = 'HTML Request Error'
            end_date = 'HTML Request Error'
        except Exception as e:
            # Catch-all for other potential errors during HTML processing
            print(f"An unexpected error occurred during HTML fetching/JS parsing: {e}")
            start_date = 'General Parsing Error'
            end_date = 'General Parsing Error'

    else:
        # This case should ideally not be reached if API call was successful
        print("Cannot fetch warranty page because Product ID path is missing.")
        return None

    return {
        "model": model,
        "start_date": start_date,
        "end_date": end_date
    }


# --- Main Execution ---
if __name__ == "__main__":
    # Use the serial number that worked before OR the one from your original HTML

    if len(sys.argv) < 2:
        print("Usage: python index2.py <serial_number>")
        sys.exit(1) # Exit if no serial number is provided

    serial = sys.argv[1] # Get the serial number from the first command-line argument
    # serial = "1S62AEKAR2LAVNA90AT9" # The one from your Selenium example (keep as comment or remove)

    print(f"Attempting to get warranty info for SN: {serial}")
    warranty_data = get_lenovo_warranty_info(serial)

    if warranty_data:
        print("-" * 20)
        print(f"Serial Number: {serial}")
        print(f"Model: {warranty_data['model']}")
        print(f"Warranty Start Date: {warranty_data['start_date']}")
        print(f"Warranty End Date: {warranty_data['end_date']}")
        print("-" * 20)
    else:
        print(f"Failed to retrieve complete information for serial number: {serial}")