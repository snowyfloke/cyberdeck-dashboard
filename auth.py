import os
import requests
import spotipy
from dotenv import load_dotenv

load_dotenv()

def refresh_acess_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.getenv("REFRESH_CODE"),
        },
        auth=(
            os.getenv("SPOTIFY_CLIENT_ID"),
            os.getenv("SPOTIFY_CLIENT_SECRET")
        )
    )

    response.raise_for_status()
    return response.json()["access_token"]


def get_spotify_client():
    token = refresh_acess_token()
    return spotipy.Spotify(auth=token)
