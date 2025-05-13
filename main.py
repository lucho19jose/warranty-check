from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Added import
import uvicorn
from warrantylenovoo import get_lenovo_warranty_info # Import the function

app = FastAPI(
    title="Lenovo Warranty Check API",
    description="An API to check Lenovo warranty status using a serial number.",
    version="1.0.0",
)

# CORS Middleware Configuration
origins = [
    "http://127.0.0.1:5500",  # Your local frontend development server
    "http://localhost:5500",   # Another common local dev origin
    # Add any other origins you need to allow, like your production frontend URL
    # "https://your-production-frontend.com", 
    # Using "*" will allow all origins, but be more specific in production
     "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Can be a list of origins or "*" for all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

@app.get("/warranty/{serial_number}")
async def check_warranty(serial_number: str):
    """
    Retrieves warranty information for the given Lenovo serial number.
    """
    print(f"API endpoint called for SN: {serial_number}") # Add logging
    warranty_data = get_lenovo_warranty_info(serial_number)

    if warranty_data:
        # Ensure 'model' and 'warranties' keys exist, providing defaults for safety.
        # get_lenovo_warranty_info should always return these if not None.
        model_name = warranty_data.get('model', 'N/A')
        warranties_list = warranty_data.get('warranties', [])

        model_is_na = model_name == 'N/A'
        
        has_warranty_errors = False
        first_error_name = "Unknown Error" 

        if not isinstance(warranties_list, list):
            # This case should ideally not happen if get_lenovo_warranty_info is correct.
            print(f"Warning: 'warranties' field is not a list for SN {serial_number}. Data: {warranty_data}")
            has_warranty_errors = True
            first_error_name = "InvalidWarrantyDataStructure"
        elif warranties_list: # Check if the list is not empty
            for item in warranties_list:
                # Ensure item is a dictionary before trying to get 'is_error'
                if isinstance(item, dict) and item.get('is_error'):
                    has_warranty_errors = True
                    first_error_name = item.get('name', 'Unknown Error')
                    break 
        
        should_raise_404 = False
        error_message = "Could not retrieve complete warranty information."

        # Condition 1: Model is N/A AND (warranty list is empty OR contains errors)
        # This suggests the product itself wasn't properly identified or resolved.
        if model_is_na and (not warranties_list or has_warranty_errors):
            should_raise_404 = True
            error_message = "Product information not found or incomplete."
            if has_warranty_errors:
                 error_message += f" Specific issue: {first_error_name}."
        # Condition 2: Model is found, BUT there are explicit errors in the warranty list.
        # This suggests product was identified, but fetching its warranty details failed.
        elif not model_is_na and has_warranty_errors:
            should_raise_404 = True
            error_message = f"Failed to retrieve warranty details: {first_error_name}."
        
        if should_raise_404:
            print(f"Raising 404 for SN {serial_number} due to: {error_message}. Data: {warranty_data}")
            raise HTTPException(status_code=404, detail={"message": error_message, "data": warranty_data})

        # If no 404 conditions met, data is considered valid.
        # This includes model found + warranties found, or model found + empty warranties list (no errors).
        print(f"Successfully retrieved data for {serial_number}: {warranty_data}")
        return warranty_data
    else:
        # This happens if get_lenovo_warranty_info returned None (critical API failure at Step 1)
        print(f"Warranty function returned None for {serial_number}")
        raise HTTPException(status_code=404, detail="Product not found or initial API request failed.")

# Add a root endpoint for basic check
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Lenovo Warranty Check API. Use /warranty/{serial_number} to check warranty."}

if __name__ == "__main__":
    # Run the app with uvicorn
    # host="0.0.0.0" makes it accessible on the network
    # reload=True automatically restarts the server on code changes (good for development)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)