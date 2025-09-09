import requests

url = "http://127.0.0.1:5000/codegen"
data = {"prompt": "Write a Python function to reverse a string"}

try:
    response = requests.post(url, json=data)
    print("Status code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
