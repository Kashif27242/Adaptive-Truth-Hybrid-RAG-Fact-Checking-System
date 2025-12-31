import requests
import json
import time

url = "http://localhost:8000/verify"
headers = {"Content-Type": "application/json"}

def test_claim(claim, type_desc):
    print(f"\n--- Testing {type_desc} Claim: '{claim}' ---")
    payload = {"claim": claim}
    try:
        start = time.time()
        response = requests.post(url, json=payload, headers=headers)
        duration = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"Verdict: {result.get('verdict')}")
            print(f"Time Taken: {duration:.2f}s")
            print("Evidence Sources:")
            for e in result.get('evidence', []):
                print(f" - {e.get('source')} (Conf: {e.get('confidence')})")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    # 1. Historical Fact (Should prioritize Local if available)
    test_claim("The Roman Empire fell in 476 AD", "Historical")
    
    # 2. Modern Event (Should trigger Web Search)
    test_claim("The 2024 Olympics were held in Paris", "Time-Sensitive")
