import http.client
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AMBEE_KEY")

conn = http.client.HTTPSConnection("api.ambeedata.com")

headers = {
    'x-api-key': api_key,
    'Content-type': "application/json"
}

conn.request("GET", "/weather/latest/by-lat-lng?lat=12.9889055&lng=77.574044", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))