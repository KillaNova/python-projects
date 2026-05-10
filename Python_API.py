import requests
import json
import os

try:
    response = requests.get("https://api.coinbase.com/v2/prices/BTC-EUR/spot")
    response.raise_for_status()
    data = response.json()
    prijs = data["data"]["amount"]
    print(f"BTS prijs: €{prijs}")


except Exception as e:
    print(f"Fout: {e}")
