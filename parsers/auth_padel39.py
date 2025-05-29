import requests

def get_token_padel39(email: str, password: str) -> str:
    url = "https://playtomic.io/api/v3/auth/login"
    payload = {"email": email, "password": password}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()

    if "access_token" not in data:
        raise Exception("Не удалось получить токен")

    return data["access_token"]