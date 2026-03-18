from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from warrantylenovoo import get_lenovo_warranty_info # Import the function
from ultra_fast_warranty import extract_warranty_ultra_fast # Import the function
import re

app = FastAPI(
    title="Lenovo Warranty Check API",
    description="An API to check Lenovo warranty status using a serial number.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

def determinar_marca_por_serial(serial_number):
    if not serial_number or not isinstance(serial_number, str):
        return "Dato no válido"

    serial = serial_number.strip().upper()
    serial = serial.replace("\n", "")
    if serial.startswith('"') and serial.endswith('"'):
        serial = serial[1:-1]

    invalid_serials = {"N/A", "", "DESKTOP", "NINGUNO", "USB有线鼠标"}
    if serial in invalid_serials or not serial:
        return "Dato no válido"

    # --- Dell Patterns ---
    if serial.startswith("ZZQYH") and len(serial) == 15:
        return "Dell"
    if len(serial) == 7 and serial.isalnum() and not serial.isdigit():
        if re.search(r"[A-Z]", serial) and re.search(r"[0-9]", serial):
            return "Dell"
        if serial.isalpha(): # e.g. SERVICE
            return "Dell"
    if len(serial) == 12:
        if serial.startswith(("507NT", "909NT", "608NT")):
            if serial == "909NTUW7K902": return "Dell" # Specific Dell
            if serial == "608NTEPC4988": return "Dell" # Specific Dell
            if serial.startswith("507NT"): return "Dell" # 507NTLE9B712
            # Other 909NT and 608NT might be HP/Lenovo
    if serial.startswith("AQCI") and len(serial) == 13 and serial == "AQCI11A001192": # Specific Dell
        return "Dell"


    # --- HP Patterns ---
    # Corrected 10-char HP prefixes to include 1CR
    hp_10char_prefixes = ("CND", "MXL", "1CZ", "5CD", "4CE", "8CG", "3CM", "6CM", "1CR")
    if len(serial) == 10 and serial.startswith(hp_10char_prefixes):
        return "HP" # This will now catch 1CR9160GKM as HP

    if serial.startswith("APBH") and len(serial) == 13:
        return "HP"
    if serial.startswith("V8C9H") and len(serial) == 16:
        return "HP"
    if serial.startswith("AQCI") and len(serial) == 13: # AQCI11A001006 (HP)
        return "HP" # General AQCI for HP if not specific Dell

    if len(serial) == 12:
        hp_12char_prefixes = ("011UX", "603NT", "312ND", "610NT", "409ND", "505NT", "107LT", "808NT")
        if serial.startswith(hp_12char_prefixes):
            return "HP"
        if serial.startswith("909NT") and serial != "909NTUW7K902" and not serial.startswith("909NTNHJ"): # Avoid Dell and a Lenovo one
            return "HP" # e.g., 909NTXR5K026

    # Removed V5TW from HP 8-char, it's now Lenovo
    # HP 8-char patterns are less common or conflict heavily. Most 8-chars starting V... are now Lenovo.

    # --- Lenovo Patterns ---
    if serial.startswith("20MK") and len(serial) == 8:
        return "Lenovo"
    if (serial.startswith("CN-0") or serial.startswith("CN-O")) and serial.count('-') >= 3 and len(serial) > 20:
        return "Lenovo"
    if serial.startswith("1S") and (len(serial) == 20 or len(serial) == 22 or len(serial) == 24):
        return "Lenovo"
    if serial.startswith("8SS") and len(serial) == 24:
        return "Lenovo"

    # Standard and New 8-char Lenovo prefixes (V5TW, VNA, V90C are now firmly Lenovo)
    lenovo_8char_prefixes_original = ("MJ", "PC", "YL", "S1", "PW", "LR")
    lenovo_8char_prefixes_new = ("V5TD", "VNA", "V90C", "V5TW") # Corrected: VNA (not VNA9), V5TW added
    all_lenovo_8char_prefixes = lenovo_8char_prefixes_original + lenovo_8char_prefixes_new

    if len(serial) == 8 and serial.startswith(all_lenovo_8char_prefixes):
        return "Lenovo" # This will now catch V90C..., VNA..., V5TW... as Lenovo

    if serial.startswith("PF") and (len(serial) == 8 or len(serial) == 10) and serial.isalnum():
        return "Lenovo"

    # Lenovo 10-char (1CR removed, as it's now HP based on your correction)
    if len(serial) == 10:
        if serial.startswith("CN") and not serial.startswith("CND"): # e.g. CN405225XM
            return "Lenovo"

    if len(serial) == 12:
        lenovo_12char_prefixes = ("105NT", "608NT", "506NT", "908NT", "909NTNHJ", "605NT") # Made 909NT more specific
        if serial.startswith(lenovo_12char_prefixes):
             if serial != "608NTEPC4988": # Avoid specific Dell
                return "Lenovo"

    if serial.startswith("0ATS") and len(serial) == 15:
        return "Lenovo"
    if serial.startswith("UK0A") and len(serial) == 17: # UK0A1615013283BKK (Lenovo)
        return "Lenovo"


    # --- Acer Patterns ---
    if serial.startswith("NHQ") and len(serial) > 15:
        return "Acer"

    # --- Fallback for UK0A if not Lenovo (could be HP) ---
    if serial.startswith("UK0A") and len(serial) == 17: # e.g. UK0A1615012566K69 (HP)
        return "HP" # If not caught by Lenovo's UK0A rule

    # --- Fallback for ambiguous patterns ---
    if len(serial) == 12 and serial.startswith("60"):
        if serial.startswith("603NT"): return "HP"
        if serial.startswith("608NT") or serial.startswith("605NT"):
            if serial == "608NTEPC4988": return "Dell"
            return "Lenovo"
        return "Desconocido (Ambiguo 60...)"

    return "Desconocido"


@app.get("/warranty/{serial_number}")
async def check_warranty(serial_number: str):
    """
    Retrieves warranty information for the given Lenovo serial number.
    """
    print(f"API endpoint called for SN: {serial_number}") # Add logging

    # Determine the brand based on the serial number
    brand = determinar_marca_por_serial(serial_number)

    # Lenovo or HP
    if brand not in ["Lenovo", "HP"]:
        print(f"Unsupported brand for SN {serial_number}: {brand}")
        raise HTTPException(status_code=400, detail=f"Unsupported brand: {brand}")
    if brand == "HP":
        # If it's HP, use the ultra-fast warranty check
        print(f"Using ultra-fast warranty check for HP SN: {serial_number}")
        warranty_data = extract_warranty_ultra_fast(serial_number)
        if not warranty_data or "error" in warranty_data:
            detail = warranty_data.get("error", "Warranty information not found") if warranty_data else "Warranty information not found"
            raise HTTPException(status_code=404, detail=detail)
        # Normalize HP response to match Lenovo format
        return {
            "Brand": "HP",
            "Product Name": warranty_data.get("product_name", "N/A") or "N/A",
            "Serial Number": warranty_data.get("serial_number", serial_number),
            "Warranty Start": warranty_data.get("warranty_start", "N/A") or "N/A",
            "Warranty End": warranty_data.get("warranty_end", "N/A") or "N/A",
        }
    elif brand == "Lenovo":
        warranty_data = get_lenovo_warranty_info(serial_number)

        if isinstance(warranty_data, dict) and "data" in warranty_data:
            machine_info = warranty_data["data"].get("machineInfo", {})
            current_warranty = warranty_data["data"].get("currentWarranty", {})
            
            # Extract the specific fields you want
            # Format dates from yyyy-mm-dd to dd/mm/yyyy
            start_date = current_warranty.get("startDate", "N/A")
            end_date = current_warranty.get("endDate", "N/A")
            
            formatted_start = "N/A"
            formatted_end = "N/A"
            
            if start_date != "N/A":
                try:
                    formatted_start = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                except ValueError:
                    formatted_start = start_date
            
            if end_date != "N/A":
                try:
                    formatted_end = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                except ValueError:
                    formatted_end = end_date
            
            simplified_response = {
                "Brand": "Lenovo",  # or you could use machine_info.get("brand", "Lenovo")
                "Product Name": machine_info.get("productName", "N/A"),
                "Serial Number": machine_info.get("serial", serial_number),
                "Warranty Start": formatted_start,
                "Warranty End": formatted_end
            }
            
            return simplified_response
        else:
            print(f"Error retrieving warranty data for SN {serial_number}: {warranty_data}")
            raise HTTPException(status_code=500, detail="Error retrieving warranty information.")
    
# Add a root endpoint for basic check
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Lenovo Warranty Check API. Use /warranty/{serial_number} to check warranty."}

if __name__ == "__main__":
    # Run the app with uvicorn
    # host="0.0.0.0" makes it accessible on the network
    # reload=True automatically restarts the server on code changes (good for development)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)