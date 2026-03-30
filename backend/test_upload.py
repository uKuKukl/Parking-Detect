import requests
import sys

url = "http://localhost:8080/api/violations/upload-image"
image_path = r"d:\Program Files\Parking-Detect\backend\uploads\1774692815841_test1.jpg"

try:
    with open(image_path, 'rb') as f:
        files = {'file': ('test1.jpg', f, 'image/jpeg')}
        data = {'roiId': '1'}
        print("Uploading to", url)
        res = requests.post(url, files=files, data=data)
        print("Status Code:", res.status_code)
        print("Response:", res.text)
except Exception as e:
    print("Error:", e)
