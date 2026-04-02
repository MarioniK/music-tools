import requests


CLASSIFIER_URL = "http://genre-classifier:8021/classify"


def classify_audio(file_path):

    with open(file_path, "rb") as f:

        files = {"file": f}

        r = requests.post(CLASSIFIER_URL, files=files)

    if r.status_code != 200:
        return None

    data = r.json()

    return {
        "raw": data.get("genres", []),
        "normalized": data.get("genres_pretty", [])
    }