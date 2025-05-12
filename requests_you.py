import requests
import json

# 1. URL
url = "https://pcsupport.lenovo.com/us/en/api/v4/upsell/redport/getIbaseInfo"

# 2. Headers
# WARNING: X-CSRF-Token and Cookie are highly dynamic.
# These hardcoded values will likely fail for a new session.
# You would normally manage these with a requests.Session() and by
# first fetching a page to get a valid token and cookies.
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,es-US;q=0.8,es;q=0.7",
    "Content-Type": "application/json",
    # The Cookie is extremely long and session-specific. Truncated for display.
    # For a real script, let requests.Session() handle this.
    "Cookie": "ETCR=true; s_ecid=MCMID%7C80850080314687095279211903795356993526; ... (rest of your very long cookie string) ... RAZrd4SuIkY6/Q==~1",
    "Origin": "https://pcsupport.lenovo.com",
    "Referer": "https://pcsupport.lenovo.com/us/en/products/desktops-and-all-in-ones/thinkcentre-m-series-desktops/thinkcentre-m70s-gen-3/11t7/11t7s1d900/mj0jczz8/warranty/?linkTrack=Caps:Body_SearchProduct&searchType=6&keyWordSearch=MJ0JCZZ8",
    "Sec-CH-UA": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "X-CSRF-Token": "3s8lU3DMHAxuvRdMl01Ymc", # DYNAMIC!
    "X-Requested-Timezone": "America/Lima", # May or may not be strictly necessary
    "X-Requested-With": "XMLHttpRequest"
}

# 3. Payload (Body of the POST request)
# This was reconstructed to match content-length: 79 and typical data from the Referer.
payload = {
    "country": "us",
    "language": "en",
    "machineType": "11T7",      # From Referer path part
    "serialNumber": "MJ0JCZZ8"  # From Referer path part / query param
}

# To make this more robust, you'd use a session:
# s = requests.Session()
# First, you might need to make a GET request to the referer URL (or similar page)
# using s.get(...) to allow the session to pick up necessary cookies and
# potentially parse the X-CSRF-Token from the HTML response.
# Then, update headers['Cookie'] (or let session handle) and headers['X-CSRF-Token']
# response = s.post(url, headers=headers, json=payload)

# For a direct attempt with the (likely stale) headers:
print("Making POST request to:", url)
# print("Headers:", json.dumps(headers, indent=2)) # For debugging headers
# print("Payload:", json.dumps(payload, indent=2)) # For debugging payload

try:
    response = requests.post(url, headers=headers, json=payload, timeout=15) # json=payload auto-sets Content-Type if not present and serializes dict to JSON

    # 4. Check the response
    print(f"\nStatus Code: {response.status_code}")

    # Try to print JSON response, fall back to text if not JSON
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.JSONDecodeError:
        print("Response is not JSON. Response Text:")
        print(response.text)
    except Exception as e_parse:
        print(f"An error occurred parsing response: {e_parse}")
        print("Raw Response Text:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"An error occurred during the request: {e}")

print("\n--- Important Considerations for a working script ---")
print("1. Dynamic Headers: 'Cookie' and 'X-CSRF-Token' are critical and dynamic.")
print("   - Use `requests.Session()` to manage cookies.")
print("   - Fetch the 'X-CSRF-Token' from a preceding GET request to a relevant page (it's often in a meta tag or a cookie).")
print("2. Payload: The payload used here was reconstructed. If it's incorrect, the API might return an error. The browser's developer tools (Network tab) are the best source for the exact payload sent during a live session.")