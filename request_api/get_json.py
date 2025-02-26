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
    reference_no = "Enter Ref No"
    token = "Enter Token"
    get_transaction(reference_no, token)
