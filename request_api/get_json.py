import requests
import os

def get_transaction(reference_no, token):
    if token is None:
        print("No valid token available. Exiting get_transaction.")
        return

    url = f"http://127.0.0.1:8001/transactions/{reference_no}?token={token}"
    response = requests.get(url)

    get_json_path = r"C:\Users\A200204474\pythonProjects\fastApi\fastApiProject\request_api\get.json"

    # Ensure the directory exists
    os.makedirs(os.path.dirname(get_json_path), exist_ok=True)

    # Write response to file
    with open(get_json_path, 'w') as data:
        data.write(response.text)

    print("Status:", response.status_code)
    print("Response:", response.text)


if __name__ == "__main__":
    reference_no = "e5867396-e509-49c0-a1c0-c5f2a2b7a049"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHJpbmciLCJleHAiOjE3Mzk2OTQ0MTd9.ZRp8NckTWycsJTtFJmOe3DFkIJL7S1UhKfKsIqa_8Ow"
    get_transaction(reference_no, token)
