import requests
import sys
import re
import json

def get_lenovo_warranty_info(serial_number):
    """
    Fetches warranty information for a given Lenovo serial number using:
    1. API call to get product ID, Model, and Machine Type Group.
    2. POST API call to getIbaseInfo for detailed warranty data.

    Args:
        serial_number (str): The serial number of the Lenovo device.

    Returns:
        dict: A dictionary containing "model" (str) and "warranties" (list of dicts).
              Each warranty dict contains details like id, name, start_date, end_date, status, type, description.
              Returns None if the initial product API call fails critically.
              The "warranties" list can be empty or contain error dictionaries.
    """
    product_api_url = f"https://pcsupport.lenovo.com/us/en/api/v4/mse/getproducts?productId={serial_number}"
    model = 'N/A'
    product_id_full = None # Renamed from product_id_path for clarity
    machine_type_group = "N/A"
    warranties_data = []
    response_api = None
    response_ibase_api = None

    # Headers for the initial product GET API
    get_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    }

    # --- Step 1: Call API to get Product ID, Model, and Machine Type Group ---
    try:
        print(f"Calling API to get product details: {product_api_url}")
        response_api = requests.get(product_api_url, headers=get_headers, timeout=15)
        response_api.raise_for_status()
        data = response_api.json()

        if isinstance(data, list) and len(data) > 0:
            product_info = data[0]
            model = product_info.get('Name', 'N/A')
            product_id_full = product_info.get('Id') # e.g., /desktops-and-all-in-ones/thinkcentre-m-series-desktops/thinkcentre-m70s-gen-3/11t7/11t7s1d900/mj0jczz8
            if product_id_full:
                print(f"Product ID full from API: {product_id_full}")
                # Extract machine_type_group (e.g., "11t7" or "20qn")
                # Path is typically /category/family/series/MACHINE_TYPE_GROUP/machine_type_specific/api_serial
                path_parts = product_id_full.strip('/').split('/')
                if len(path_parts) >= 3:
                    machine_type_group = path_parts[-3] # e.g., '11t7' or '20qn'
                    print(f"Extracted Machine Type Group: {machine_type_group}")
                else:
                    print(f"Warning: product_id_full '{product_id_full}' does not have expected structure to extract machine_type_group.")
            else:
                print("Could not find 'Id' (product_id_full) in API response. Warranty lookup might fail.")
        else:
            print(f"Product not found or unexpected JSON structure from product API: {data}")
            return {"model": model, "warranties": [{"name": "Product API Error", "error_detail": "Product not found or unexpected structure.", "is_error": True}]}

    except requests.exceptions.RequestException as e:
        print(f"Error during product API request to {product_api_url}: {e}")
        if response_api is not None: print(f"API Status Code: {response_api.status_code}, Text: {response_api.text[:200]}...")
        return None
    except ValueError as e:
        print(f"Error decoding product API JSON response: {e}")
        if response_api is not None: print(f"API Response Text: {response_api.text[:200]}...")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during product API call: {e}")
        return None

    # --- Step 2: Call new POST API to get IbaseInfo (includes all warranties) ---
    if machine_type_group == "N/A" or not product_id_full:
        print("Cannot fetch warranty details using getIbaseInfo API because Machine Type Group or Product ID is missing.")
        return {"model": model, "warranties": [{"name": "Prerequisite Missing", "error_detail": "Machine Type Group or Product ID not available for getIbaseInfo.", "is_error": True}]}

    ibase_api_url = "https://pcsupport.lenovo.com/us/en/api/v4/upsell/redport/getIbaseInfo"
    referer_url = f"https://pcsupport.lenovo.com/us/en/products{product_id_full}/warranty/" # Note: product_id_full starts with '/'

    # WARNING: The x-csrf-token is DYNAMIC. This hardcoded token will likely fail.
    # You need to fetch a fresh token for each session, typically from a GET request
    # to a page on pcsupport.lenovo.com using a requests.Session().
    csrf_token_from_your_test = '3s8lU3DMHAxuvRdMl01Ymc' # THIS IS THE CRITICAL DYNAMIC VALUE

    post_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://pcsupport.lenovo.com',
        'Referer': referer_url,
        'x-csrf-token': csrf_token_from_your_test, # DYNAMIC - VERY LIKELY TO BECOME INVALID
        'x-requested-timezone': 'America/Lima', # As seen in your request
        'x-requested-with': 'XMLHttpRequest',
        # 'Cookie': 'YOUR_VERY_LONG_DYNAMIC_COOKIE_STRING_HERE' # Cookies are also crucial and dynamic.
                                                            # Best managed with requests.Session()
    }

    payload = {
        "country": "us",
        "language": "en",
        "machineType": machine_type_group,
        "serialNumber": serial_number
    }
    # print(f"DEBUG: Payload for getIbaseInfo: {json.dumps(payload)}") # For debugging

    print(f"Calling getIbaseInfo API: {ibase_api_url}")
    try:
        response_ibase_api = requests.post(ibase_api_url, headers=post_headers, json=payload, timeout=20)
        response_ibase_api.raise_for_status()
        ibase_data = response_ibase_api.json()

        print(f"DEBUG: Full JSON response from getIbaseInfo API for SN {serial_number}:")
        print(json.dumps(ibase_data, indent=2)) # Print the full structure for verification

        # --- Parse ibase_data ---
        # The structure of ibase_data needs to be confirmed from the DEBUG output.
        # Assuming a structure like: { "success": true, "data": { "baseWarranties": [...] } }
        # or directly a list under a key, or keys like "currentWarranties", "allWarranties" etc.
        
        # Common patterns for warranty lists in such APIs:
        # ibase_data.get("data", {}).get("baseWarranties", [])
        # ibase_data.get("data", {}).get("warrantyInfo", [])
        # ibase_data.get("warranties", [])
        # ibase_data.get("list", [])

        # Let's try to find a list of warranties. Checking common top-level keys first.
        raw_warranty_list = None
        if isinstance(ibase_data, list):
            raw_warranty_list = ibase_data
        elif isinstance(ibase_data, dict):
            # Try common patterns observed or guessed for such APIs
            possible_keys = ["baseWarranties", "warrantyList", "warranties", "data", "items"]
            for key in possible_keys:
                potential_list = ibase_data.get(key)
                if isinstance(potential_list, list):
                    raw_warranty_list = potential_list
                    print(f"Found warranty list under key: '{key}'")
                    break
                elif isinstance(potential_list, dict): # e.g. if data is nested like data.baseWarranties
                    nested_keys = ["baseWarranties", "warrantyInfo", "list"]
                    for n_key in nested_keys:
                        deep_list = potential_list.get(n_key)
                        if isinstance(deep_list, list):
                            raw_warranty_list = deep_list
                            print(f"Found warranty list under nested key: '{key}.{n_key}'")
                            break
                    if raw_warranty_list:
                        break
        
        if raw_warranty_list is not None:
            print(f"Processing {len(raw_warranty_list)} potential warranty entries.")
            for item in raw_warranty_list:
                if not isinstance(item, dict):
                    print(f"Skipping non-dictionary item in warranty list: {item}")
                    continue
                
                # Map fields based on screenshot and common API naming
                # Adjust these .get() keys based on the actual JSON from DEBUG output
                warranty_entry = {
                    "id": item.get('id', item.get('warrantyId', 'N/A')),
                    "name": item.get('name', item.get('title', item.get('warrantyName', 'N/A'))),
                    "start_date": item.get('startDate', item.get('start', 'N/A')),
                    "end_date": item.get('endDate', item.get('end', 'N/A')),
                    "status": item.get('status', item.get('statusDescription', item.get('warrantyStatus', 'N/A'))),
                    "type": item.get('type', item.get('typeDescription', item.get('warrantyType', 'N/A'))),
                    "description": item.get('description', item.get('longDescription', 'N/A'))
                }
                warranties_data.append(warranty_entry)
            if not warranties_data and raw_warranty_list:
                 print("Found a list for warranties, but items might not be in expected dict format or keys mismatched.")
                 warranties_data.append({"name": "Parsing Ambiguity", "error_detail": "Found list but failed to parse items.", "raw_list_sample": raw_warranty_list[:2], "is_error": True})
            elif not raw_warranty_list:
                 print("Could not find a list of warranties in the response JSON using common key patterns.")
                 warranties_data.append({"name": "Warranty List Not Found", "error_detail": "No list of warranties identified in JSON.", "raw_response_sample": str(ibase_data)[:500], "is_error": True})


        else:
            print("Failed to identify a list of warranties in the getIbaseInfo response JSON structure.")
            warranties_data.append({"name": "IbaseAPI Structure Error", "error_detail": "Could not find warranty list in response.", "raw_response": str(ibase_data)[:500], "is_error": True})

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error during getIbaseInfo API request: {e}")
        error_detail = str(e)
        if response_ibase_api is not None:
            print(f"getIbaseInfo API Status Code: {response_ibase_api.status_code}")
            print(f"getIbaseInfo API Response Text: {response_ibase_api.text[:500]}...")
            error_detail += f" | Status: {response_ibase_api.status_code}, Response: {response_ibase_api.text[:200]}"
        warranties_data.append({"name": "IbaseAPI HTTP Error", "error_detail": error_detail, "is_error": True})
    except requests.exceptions.RequestException as e:
        print(f"Generic error during getIbaseInfo API request: {e}")
        warranties_data.append({"name": "IbaseAPI Request Error", "error_detail": str(e), "is_error": True})
    except ValueError as e: # Catches JSON decoding errors
        print(f"Error decoding getIbaseInfo API JSON response: {e}")
        raw_text = response_ibase_api.text if response_ibase_api is not None else "N/A"
        print(f"getIbaseInfo API Response Text: {raw_text[:500]}...")
        warranties_data.append({"name": "IbaseAPI JSON Error", "error_detail": str(e), "raw_text": raw_text[:200], "is_error": True})
    except Exception as e:
        print(f"An unexpected error occurred during getIbaseInfo API call or parsing: {e}")
        warranties_data.append({"name": "IbaseAPI Unexpected Error", "error_detail": str(e), "is_error": True})

    return {
        "model": model,
        "warranties": warranties_data
    }


# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python your_script_name.py <serial_number>")
        sys.exit(1)

    serial = sys.argv[1]
    print(f"Attempting to get warranty info for SN: {serial}")
    result_data = get_lenovo_warranty_info(serial)

    if result_data:
        print("\n" + "=" * 30)
        print(f"FINAL RESULTS FOR SERIAL: {serial}")
        print(f"Model: {result_data['model']}")
        print("=" * 30)

        if not result_data['warranties']:
            print("No warranty information entries found or processed.")
        else:
            # Check if the list contains only error/placeholder entries
            actual_warranties_found = False
            for entry in result_data['warranties']:
                if not entry.get('is_error') and not entry.get('is_placeholder'):
                    actual_warranties_found = True
                    break
            
            if not actual_warranties_found:
                print("No actual warranty details parsed. Errors or placeholders listed below:")
                for i, entry in enumerate(result_data['warranties']):
                    print(f"\n  Entry #{i+1} (Error/Placeholder):")
                    print(f"    Name/Type: {entry.get('name', 'Unknown Entry')}")
                    if entry.get('error_detail'):
                        print(f"    Details: {entry.get('error_detail')}")
                    if entry.get('raw_response_sample'):
                         print(f"    Raw Sample: {entry.get('raw_response_sample')}")
                    if entry.get('raw_list_sample'):
                         print(f"    Raw List Sample: {entry.get('raw_list_sample')}")
                    if entry.get('raw_text'):
                         print(f"    Raw Text Sample: {entry.get('raw_text')}")


            else:
                print(f"Found {len([w for w in result_data['warranties'] if not w.get('is_error')])} warranty entries:")
                for i, warranty in enumerate(result_data['warranties']):
                    if warranty.get('is_error') or warranty.get('is_placeholder'): # Skip explicit error/placeholder items in final good list
                        continue

                    print(f"\n  Warranty #{i+1}:")
                    print(f"    Name: {warranty.get('name', 'N/A')}")
                    print(f"    ID: {warranty.get('id', 'N/A')}")
                    print(f"    Status: {warranty.get('status', 'N/A')}")
                    print(f"    Type: {warranty.get('type', 'N/A')}")
                    print(f"    Start Date: {warranty.get('start_date', 'N/A')}")
                    print(f"    End Date: {warranty.get('end_date', 'N/A')}")
                    description = warranty.get('description', 'N/A')
                    print(f"    Description: {str(description)[:150]}{'...' if len(str(description)) > 150 else ''}")
        print("=" * 30)
    else:
        print(f"Failed to retrieve any product information (including model) for serial number: {serial}")