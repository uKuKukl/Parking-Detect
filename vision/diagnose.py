import traceback
import requests

try:
    print("=== Testing Backend Connectivity ===")
    
    print("\n1. GET /api/violations/pending")
    r1 = requests.get('http://localhost:8080/api/violations/pending')
    print("Status:", r1.status_code)
    print("Reason:", r1.reason)
    print("Headers:", r1.headers)
    print("Body:", r1.text[:500])

    print("\n2. GET /api/violations/reports")
    r2 = requests.get('http://localhost:8080/api/violations/reports')
    print("Status:", r2.status_code)
    print("Reason:", r2.reason)
    print("Headers:", r2.headers)
    print("Body:", r2.text[:500])
    
except Exception as e:
    print("Exception occurred:")
    traceback.print_exc()
