import requests
import time

def test_kids_endpoint():
    start = time.time()
    try:
        print("Requesting /api/kids...")
        resp = requests.get("http://localhost:8000/api/kids", timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}...")
        print(f"Time: {time.time() - start:.4f}s")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_kids_endpoint()
