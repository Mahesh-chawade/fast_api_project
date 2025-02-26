import requests

def post_data(token):
    url = f"http://127.0.0.1:8001/transactions/?token={token}"

    data = {
        "date": "2024-11-12",
        "details": "Debit",
        "debit": 110,
        "credit": 230
    }

    response = requests.post(url,json=data)

    print(response.status_code)
    print(response.text)

if __name__ == "__main__":
    token = "use your token"
    post_data(token)
