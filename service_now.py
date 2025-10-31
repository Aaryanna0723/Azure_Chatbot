import requests
from dotenv import load_dotenv
import os

load_dotenv()
# ServiceNow instance details

BASE_URL = os.getenv("SERVICENOW_INSTANCE_URL")
CLIENT_ID = os.getenv("SERVICENOW_CLIENT_ID")
CLIENT_SECRET = os.getenv("SERVICENOW_CLIENT_SECRET")


# Step 1: Get OAuth token

def get_oauth_token():
    url = f"{BASE_URL}/oauth_token.do"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, data=payload,verify=False)
    try:
        if response.status_code == 200:
        #if response.raise_for_status():
            token = response.json().get("access_token")
            print("Token Response:", response.json())
            return token
        else:
            print(f"Error get_oauth_token: {response.status_code} - {response.text}")
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        print(f"Exception occurred while get_oauth_token: {e}")
        return "Error: Unable to generate token"



# Step 2: GET incidents

def get_incidents(token):
    url = f"{BASE_URL}/api/now/table/incident"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers,verify=False)
    response.raise_for_status()
    return response.json()



# Step 3: POST new incident
def create_incident(short_description, description):
    token = get_oauth_token()
    url = f"{BASE_URL}/api/now/table/incident"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "short_description": short_description,
        "description": description
    }

    response = requests.post(url, headers=headers, json=payload,verify=False)
    try:
        if response.status_code==201:
            result = response.json()["result"]
            #return f"Incident created: {result['number']} (Sys ID: {result['sys_id']})"
            return result["number"]
        else:
            print(f"Error create_incident: {response.status_code} - {response.text}")
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        print(f"Exception occurred while create_incident: {e}")
        return "Error: Unable to create incident"

 