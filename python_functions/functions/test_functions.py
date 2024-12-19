import requests
import json

def test_cs_advisor(message, thread_id=None):
    url = "http://localhost:5001/gpt-advisor/us-central1/cs_advisor"
    
    # Prepare the request payload
    payload = {
        "message": message,
        "threadId": thread_id
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
    # print("=== Test 1: Asking about prerequisites ===")
    # test_cs_advisor("What are the prerequisites for CS2150?")
    
    print("\n=== Test 2: Asking about a professor ===")
    test_cs_advisor("What is Professor Mark Sherriff's rating?", thread_id="thread_T3Al6U64irgG09mdAD4pYp0p")
    
    # If you want to test conversation continuity, uncomment and modify these lines:
    # thread_id = "your_thread_id_from_first_response"
    # test_cs_advisor("What about CS3140 prerequisites?", thread_id)
    