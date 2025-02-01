import requests
import json

def test_cs_advisor(input_classes, time_constraints, optimize_ratings=True):
    url = "http://127.0.0.1:5001/gpt-advisor/us-central1/csp_build_schedule"
    
    # Prepare the request payload
    payload = {
        "input_classes": input_classes,
        "optimimze_ratings": optimize_ratings,
        "time_constraints": time_constraints,
    }
    
    # Add debug printing
    print(f"\n=== Making request ===")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(url, json=payload)
        
        # Print response details
        print(f"\n=== Response ===")
        print(f"Status code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print("\nResponse content:")
        
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Raw response:", response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"\nError making request: {str(e)}")

if __name__ == "__main__":
    # Test different scenarios
    print("=== Test 1: Asking about prerequisites ===")
    test_cs_advisor(["CS 2120", "CS 2100"], ["9:00am", "5:00pm"])
    