import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Krishidhan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")

ZOHO_OAUTH_URL = "https://accounts.zoho.in/oauth/v2/token"
ZOHO_API_BASE_URL = "https://www.zohoapis.in/crm/v6"


class LeadFormModel(BaseModel):
    first_name: str
    last_name: str
    business_type: str
    mobile_number: str
    street_address: str
    city: str
    state: str
    country: str
    source_of_lead: str


def get_zoho_access_token():
    if not all([ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN]):
        raise ValueError("Missing Zoho OAuth credentials in .env file")

    payload = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }

    try:
        response = requests.post(ZOHO_OAUTH_URL, data=payload)
        response.raise_for_status()
        data = response.json()
        
        if "access_token" in data:
            return data["access_token"]
        else:
            print("OAuth error:", data)
            raise ValueError("Failed to get access token from response.")
            
    except Exception as e:
        print(f"Auth error: {e}")
        return None


@app.post("/api/submit-lead")
async def submit_lead(lead_data: LeadFormModel):
    access_token = get_zoho_access_token()
    if not access_token:
        raise HTTPException(status_code=500, detail="Authentication with Zoho failed.")
    
    # Business Type mapping: Farmer -> B2C, Dealer -> B2B
    business_type_map = {
        "Farmer": "B2C",
        "Dealer": "B2B"
    }
    mapped_type = business_type_map.get(lead_data.business_type, lead_data.business_type)

    # Precise mapping to Zoho standard API names to avoid errors
    zoho_lead_payload = {
        "data": [
            {
                "First_Name": lead_data.first_name,
                "Last_Name": lead_data.last_name,
                "Mobile": lead_data.mobile_number,
                "Lead_Type": mapped_type, 
                "Street": lead_data.street_address,
                "City": lead_data.city,
                "State": lead_data.state,
                "Country": lead_data.country,
                "Lead_Source": lead_data.source_of_lead
            }
        ]
    }

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{ZOHO_API_BASE_URL}/Leads",
            json=zoho_lead_payload,
            headers=headers
        )
        
        result = response.json()
        
        # In Zoho CRM, individual records can fail even with a 200/201 response. Look inside data[0].
        if response.status_code in [200, 201, 202]:
            record_status = result.get('data', [{}])[0].get('status', 'error')
            if record_status == 'success':
                return {"status": "success", "message": "Successfully created lead."}
            else:
                # The record failed for a formatting reason
                details = result.get('data', [{}])[0].get('details', {})
                print(f"Zoho Record Level Error: {result}")
                raise HTTPException(status_code=400, detail=f"Zoho validation error: {details}")
        else:
            print(f"Zoho Header Error: {result}")
            raise HTTPException(status_code=response.status_code, detail="Submission to CRM failed due to structure.")
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Network error communicating with CRM.")

@app.get("/health")
def health_check():
    return {"status": "ok"}
