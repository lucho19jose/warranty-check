from fastapi import FastAPI, HTTPException
import uvicorn
from warrantylenovo import get_lenovo_warranty_info # Import the function

app = FastAPI(
    title="Lenovo Warranty Check API",
    description="An API to check Lenovo warranty status using a serial number.",
    version="1.0.0",
)

@app.get("/warranty/{serial_number}")
async def check_warranty(serial_number: str):
    """
    Retrieves warranty information for the given Lenovo serial number.
    """
    print(f"API endpoint called for SN: {serial_number}") # Add logging
    warranty_data = get_lenovo_warranty_info(serial_number)

    if warranty_data:
        # Check if the function returned specific error messages
        if warranty_data['start_date'] in ['BaseWarranties Not Found', 'JSON Parse Error', 'Data Processing Error', 'JS Variable Not Found', 'HTML Request Error', 'General Parsing Error'] or warranty_data['model'] == 'N/A':
             print(f"Warranty function returned partial/error data for {serial_number}: {warranty_data}")
             # Return a 404 but include the partial data for debugging/info
             raise HTTPException(status_code=404, detail={"message": "Could not retrieve complete warranty information.", "data": warranty_data})
        print(f"Successfully retrieved data for {serial_number}: {warranty_data}")
        return warranty_data
    else:
        # This happens if the initial API call in get_lenovo_warranty_info failed
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