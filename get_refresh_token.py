import os
import requests
from dotenv import load_dotenv

load_dotenv()

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REDIRECT_URI = "https://www.zoho.com"

SCOPE = "ZohoCRM.modules.ALL"

def generate_auth_url():
    if not ZOHO_CLIENT_ID:
        print("❌ ERROR: ZOHO_CLIENT_ID is not set in .env")
        return None
        
    auth_url = (
        "https://accounts.zoho.in/oauth/v2/auth"
        f"?scope={SCOPE}"
        f"&client_id={ZOHO_CLIENT_ID}"
        "&response_type=code"
        "&access_type=offline"
        "&prompt=consent"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return auth_url

def generate_refresh_token(grant_token):
    print("Exchanging Grant Token for a Refresh Token...")
    url = "https://accounts.zoho.in/oauth/v2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": grant_token
    }
    
    response = requests.post(url, data=payload)
    data = response.json()
    
    if "refresh_token" in data:
        print(f"\n✅ SUCCESS! Your Refresh Token is:\n{data['refresh_token']}\n")
        print("Please copy this refresh token and update your .env file as ZOHO_REFRESH_TOKEN !!")
    else:
        print("\n❌ ERROR generating refresh token:")
        print(data)

if __name__ == "__main__":
    print("Welcome! Let's generate your Zoho Refresh Token.\n")
    
    auth_url = generate_auth_url()
    if auth_url:
        print("--- STEP 1: GET AUTHORIZATION CODE ---")
        print("Please visit the following URL to authorize the application:")
        print(f"\n{auth_url}\n")
        print("After authorizing, you will be redirected to a URL like:")
        print(f"{REDIRECT_URI}?code=1000.xxxxxxxxx.xxxxxxxx&location=in")
        print("Copy ONLY the value of the 'code' parameter.\n")
        
        grant_token = input("--- STEP 2: ENTER CODE ---\nPlease paste the 'code' parameter here:\n> ")
        if grant_token.strip():
            generate_refresh_token(grant_token.strip())
        else:
            print("No code provided. Exiting.")
