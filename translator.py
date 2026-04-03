import requests

def translate(text, target="vi"):
    url = "https://translate.googleapis.com/translate_a/single"

    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target,
        "dt": "t",
        "q": text
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        result = response.json()
        return result[0][0][0]
    else:
        return "❌ Lỗi dịch"
