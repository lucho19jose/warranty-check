import requests
import sys # Import sys to access command-line arguments
import re # Import regular expressions
import json # Import JSON parser

def get_lenovo_warranty_info(serial_number):
    """
    Fetches warranty information for a given Lenovo serial number.
    Returns model and a list of all found warranties.

    Args:
        serial_number (str): The serial number of the Lenovo device.

    Returns:
        dict: A dictionary containing "model" (str) and "warranties" (list of dicts).
              Each warranty dict contains details like id, name, start_date, end_date, status, type, description.
              Returns None if the initial product API call fails critically.
              The "warranties" list can be empty if no warranties are found, or contain a single
              error dictionary if parsing or fetching warranty details fails.
    """
    product_api_url = f"https://pcsupport.lenovo.com/us/en/api/v4/mse/getproducts?productId={serial_number}"
    model = 'N/A'
    product_id_path = None
    response_api = None # Initialize
    response_html = None # Initialize
    warranties_data = [] # Initialize list to hold all warranty details or error info

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
        print(f"Calling API to get product details: {product_api_url}")
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
                print("Could not find 'Id' (product_id_full) in API response. Model might be available, but warranty lookup will fail.")
                # product_id_path will remain None
        else:
            print(f"Product not found or unexpected JSON structure from product API: {data}")
            # Still return model if available, but flag that warranty info might be incomplete
            return {"model": model, "warranties": [{"name": "Product API Error", "error_detail": "Product not found or unexpected structure from product API.", "is_error": True}]}

    except requests.exceptions.RequestException as e:
        print(f"Error during product API request to {product_api_url}: {e}")
        if response_api is not None:
            print(f"API Status Code: {response_api.status_code}")
            print(f"API Response Text: {response_api.text[:500]}...")
        return None # Critical failure for initial product API
    except ValueError as e: # Catches JSON decoding errors
        print(f"Error decoding product API JSON response: {e}")
        if response_api is not None:
            print(f"API Response Text: {response_api.text[:500]}...")
        return None # Critical failure for initial product API
    except Exception as e:
        print(f"An unexpected error occurred during product API call: {e}")
        return None # Critical failure for initial product API

    # --- Step 2: Call new POST API to get IbaseInfo (includes all warranties) ---
    if not product_id_path:
        print("Cannot fetch warranty details using new API because Product ID path is missing from Step 1.")
        # Return model if we have it, but indicate warranty fetching issue
        return {"model": model, "warranties": [{"name": "Product ID Path Missing", "error_detail": "Product ID path not available from initial API to fetch full warranty details.", "is_error": True}]}

    ibase_api_url = "https://pcsupport.lenovo.com/us/en/api/v4/upsell/redport/getIbaseInfo"
    # Construct a plausible referer URL. This might need adjustment if the API is strict.
    # Using the product_id_path which looks like: desktops-and-all-in-ones/thinkcentre-m-series-desktops/thinkcentre-m70s-gen-3/11x8/11x8s00h00/mj0jd8aq
    referer_url = f"https://pcsupport.lenovo.com/us/en/products/{product_id_path}/warranty/"

    post_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36', # Updated User-Agent
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://pcsupport.lenovo.com',
        'Referer': referer_url,
        'x-csrf-token': '3s8lU3DMHAxuvRdMl01Ymc', # Using the token you provided
        'x-requested-timezone': 'America/Lima', # From your provided headers
        'x-requested-with': 'XMLHttpRequest',
    }
    
    # Payload based on content-length: 79 and common patterns
    payload = {
        "serial": serial_number,
        "lang": "en", # Assuming 'en' from '/us/en/'
        "country": "us", # Assuming 'us' from '/us/en/'
        "pageSource": "warrantyChecker" # A plausible value
    }
    # Calculate actual content length for debugging, though requests handles it.
    # import json
    # print(f"DEBUG: Payload for getIbaseInfo: {json.dumps(payload)}, Length: {len(json.dumps(payload))}")


    print(f"Calling new warranty API (getIbaseInfo): {ibase_api_url}")
    try:
        response_ibase_api = requests.post(ibase_api_url, headers=post_headers, json=payload, timeout=20)
        response_ibase_api.raise_for_status()
        ibase_data = response_ibase_api.json()
        
        print(f"DEBUG: Full JSON response from getIbaseInfo API for SN {serial_number}:")
        print(json.dumps(ibase_data, indent=2))

        # Placeholder for parsing ibase_data and populating warranties_data
        # This will be the next step once we see the structure of ibase_data.
        # For now, we'll return the raw data under a temporary key or just an empty list.
        
        # Example of how you might start parsing (STRUCTURE IS UNKNOWN YET):
        # if ibase_data and ibase_data.get("success"): # Assuming a success flag
        #     raw_warranties = ibase_data.get("data", {}).get("warrantyInfo", []) # Highly speculative path
        #     for item in raw_warranties:
        #         warranty_entry = {
        #             "id": item.get('Id', item.get('warrantyId', 'N/A')), # Guessing possible field names
        #             "name": item.get('Name', item.get('title', 'N/A')),
        #             "start_date": item.get('Start', item.get('startDate', 'N/A')),
        #             "end_date": item.get('End', item.get('endDate', 'N/A')),
        #             "status": item.get('Status', item.get('statusDescription', 'N/A')),
        #             "type": item.get('Type', item.get('warrantyType', 'N/A')),
        #             "description": item.get('Description', item.get('longDescription', 'N/A'))
        #         }
        #         warranties_data.append(warranty_entry)
        # else:
        #     warranties_data.append({"name": "IbaseAPI Error", "error_detail": "Failed to get data or success flag false.", "raw_response": ibase_data, "is_error": True})

        # For now, let's just return an empty list for warranties until we know the structure
        # and confirm the API call works.
        # Or, to help with next step, put the raw response in for now:
        if ibase_data:
             warranties_data.append({"name": "RawIbaseResponse", "data": ibase_data, "is_placeholder": True})
        else:
            warranties_data.append({"name": "IbaseAPI Empty Response", "error_detail": "getIbaseInfo returned empty or non-JSON.", "is_error": True})


    except requests.exceptions.RequestException as e:
        print(f"Error during getIbaseInfo API request to {ibase_api_url}: {e}")
        error_detail = str(e)
        if response_ibase_api is not None:
            print(f"getIbaseInfo API Status Code: {response_ibase_api.status_code}")
            print(f"getIbaseInfo API Response Text: {response_ibase_api.text[:500]}...")
            error_detail += f" | Status: {response_ibase_api.status_code}, Response: {response_ibase_api.text[:200]}"
        warranties_data.append({"name": "IbaseAPI Request Error", "error_detail": error_detail, "is_error": True})
    except ValueError as e: # Catches JSON decoding errors
        print(f"Error decoding getIbaseInfo API JSON response: {e}")
        if response_ibase_api is not None:
            print(f"getIbaseInfo API Response Text: {response_ibase_api.text[:500]}...")
        warranties_data.append({"name": "IbaseAPI JSON Error", "error_detail": str(e), "raw_text": response_ibase_api.text if response_ibase_api else "N/A", "is_error": True})
    except Exception as e:
        print(f"An unexpected error occurred during getIbaseInfo API call: {e}")
        warranties_data.append({"name": "IbaseAPI Unexpected Error", "error_detail": str(e), "is_error": True})
    
    return {
        "model": model,
        "warranties": warranties_data
    }


# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python your_script_name.py <serial_number>") # Modified script name placeholder
        sys.exit(1)

    serial = sys.argv[1]
    print(f"Attempting to get warranty info for SN: {serial}")
    result_data = get_lenovo_warranty_info(serial)

    if result_data:
        print("-" * 30)
        print(f"Serial Number: {serial}")
        print(f"Model: {result_data['model']}")
        print("-" * 30)

        if not result_data['warranties']:
            print("No warranty information found or processed.")
        else:
            # Check if the first (and potentially only) entry is an error
            # This assumes error states result in a list with a single error dictionary
            first_entry = result_data['warranties'][0]
            if len(result_data['warranties']) == 1 and first_entry.get('is_error'):
                print("An error occurred while fetching/processing warranty details:")
                print(f"  Error Type: {first_entry.get('name', 'Unknown Error')}")
                print(f"  Details: {first_entry.get('error_detail', 'No additional details.')}")
            else:
                print(f"Found {len(result_data['warranties'])} warranty entries:")
                for i, warranty in enumerate(result_data['warranties']):
                    # This check is a safeguard in case an error object wasn't the only item.
                    if warranty.get('is_error'):
                        print(f"\n  Problematic Entry #{i+1}:")
                        print(f"    Error Type: {warranty.get('name', 'Unknown Error')}")
                        print(f"    Details: {warranty.get('error_detail', 'No additional details.')}")
                        continue # Skip to next item if it's an error object mixed in

                    print(f"\n  Warranty #{i+1}:")
                    print(f"    Name: {warranty.get('name', 'N/A')}")
                    print(f"    ID: {warranty.get('id', 'N/A')}")
                    print(f"    Status: {warranty.get('status', 'N/A')}")
                    print(f"    Type: {warranty.get('type', 'N/A')}")
                    print(f"    Start Date: {warranty.get('start_date', 'N/A')}")
                    print(f"    End Date: {warranty.get('end_date', 'N/A')}")
                    description = warranty.get('description', 'N/A')
                    print(f"    Description: {description[:150]}{'...' if len(description) > 150 else ''}") # Show more description
        print("-" * 30)
    else:
        # This case implies get_lenovo_warranty_info returned None (critical API failure at Step 1)
        print(f"Failed to retrieve any product information (including model) for serial number: {serial}")