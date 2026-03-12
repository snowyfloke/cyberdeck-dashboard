import urllib.request
import json

def get_system_stats(pc_ip: str) -> dict:
    try:
        url = f"http://{pc_ip}:5000/stats"
        with urllib.request.urlopen(url, timeout=3) as response:
            return json.loads(response.read())
    except Exception:
        return None
