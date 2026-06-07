import urllib.request
import json

url = "http://localhost:8001/api/v1/agent/chat"
data = {
    "user_id": 1,
    "message": "Hello Tori, can you give me a brief summary of what you can do?"
}

req = urllib.request.Request(url)
req.add_header('Content-Type', 'application/json; charset=utf-8')
jsondata = json.dumps(data)
jsondataasbytes = jsondata.encode('utf-8')
req.add_header('Content-Length', len(jsondataasbytes))

try:
    response = urllib.request.urlopen(req, jsondataasbytes)
    res_body = response.read().decode('utf-8')
    print("Response:")
    print(res_body)
except Exception as e:
    print(f"Error: {e}")
