import urllib.request
import json
import urllib.parse

def chat():
    url = "http://localhost:8001/api/v1/agent/chat"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "user_id": 1,
        "message": "Show me a budget slider for Dining at 500 RON"
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            print("Response:")
            print(res_body)
    except urllib.error.HTTPError as e:
        print(f"Error: {e.code} - {e.read().decode('utf-8')}")

if __name__ == "__main__":
    chat()
