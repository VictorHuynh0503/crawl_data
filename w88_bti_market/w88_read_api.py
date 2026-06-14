import requests

url = "http://localhost:8000/table/"  # Adjust if your FastAPI server runs on a different host/port

response = requests.get(
    url,
    params={"table": "matches"},
    timeout=60
)

response.raise_for_status()

result = response.json()

print("Rows:", result["count"])
print(result["data"][:5])