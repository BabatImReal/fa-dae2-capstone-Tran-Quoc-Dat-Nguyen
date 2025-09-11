import os
import requests
from dotenv import load_dotenv
import base64
import json
import time
from pathlib import Path

load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = requests.post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"q={artist_name}&type=artist&limit=1"

    query_url = url + "?" + query
    result = requests.get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    
    if len(json_result) == 0:
        print("No artist with this name found")
        return None
    
    return json_result[0]


def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=VN"
    headers = get_auth_header(token)
    result = requests.get(url, headers=headers)
    json_result = result.json()["tracks"]
    return json_result

def get_albums_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    headers =get_auth_header(token)
    result = requests.get(url, headers=headers)
    json_result = result.json()
    return json_result["items"]

def save_data(data: list, filename: str) -> 'Path':
    """Save data to timestamped JSON file."""
    timestamp = int(time.time())
    file_path = Path("data/external") / f"{filename}_{timestamp}.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return file_path

token = get_token()
result = search_for_artist(token, "Noo")
artist_id = result["id"]
songs = get_songs_by_artist(token, artist_id)

for idx, song in enumerate(songs):
    print(f"{idx+1}. {song['name']}")

albums = get_albums_by_artist(token, artist_id)
for idx, album in enumerate(albums):
    print(f"{idx+1}. {album['name']}")

# Save albums data as JSON
save_data(albums, f"{result['name']}_albums")