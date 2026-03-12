import urllib.request
import json

def get_weather(city: str) -> dict:
    """
    Fetches temperature and condition from wttr.in for a given city.
    Returns a dict with 'temp_c' and 'condition', or an error message.
    """
    url = f"https://wttr.in/{city}?format=j1"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())

        current = data["current_condition"][0]
        temp_c  = current["temp_C"]
        condition = current["weatherDesc"][0]["value"]

        return {"temp_c": temp_c, "condition": condition, "error": None}

    except Exception as e:
        return {"temp_c": None, "condition": None, "error": str(e)}
