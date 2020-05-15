import sys
import requests
import base64
import json
import logging
import time

client_id = "" # Client ID
client_secret = "" # Client Secret

# Spotify API
# Use the access token to access the Spotify Web API
def main():

    headers = get_headers(client_id, client_secret)

    ## Spotify Search API
    params = {
        "q": "BTS",
        "type": "artist",
        "limit": "5"
    }

    r = requests.get("https://api.spotify.com/v1/search", params=params, headers=headers)

    # 예외 처리
    try:
        r = requests.get("https://api.spotify.com/v1/search", params=params, headers=headers)
    except:
        logging.error(r.text)
        sys.exit(1) # 강제 멈춤

    r = requests.get("https://api.spotify.com/v1/search", params=params, headers=headers)

    if r.status_code != 200:
        logging.error(r.text)
        if r.status_code == 429: # To many requests
            retry_after = json.loads(r.headers)['Retry-After'] # r.headers에서 몇초를 기다려야 하는지 알 수 있다.
            time.sleep(int(retry_after))
            r = requests.get("https://api.spotify.com/v1/search", params=params, headers=headers)
        elif r.status_code == 401: # access_token expired (Authorization 만료)
            headers = get_headers(client_id, client_secret)
            r = requests.get("https://api.spotify.com/v1/search", params=params, headers=headers)
        else:
            sys.exit(1)

    # Get BTS' Albums
    r = requests.get("https://api.spotify.com/v1/artists/3Nrfpe0tUJi4K4DXYWgMUX/albums", headers=headers)

    raw = json.loads(r.text)

    total = raw['total']
    offset = raw['offset']
    limit = raw['limit']
    next = raw['next']

    albums = []
    albums.extend(raw['items']) # limit default 값이 20이므로 20개가 들어온다.
    print(next)
    print(albums)

    while next:
        r = requests.get(next, headers=headers)
        raw = json.loads(r.text)
        next = raw['next']
        print(next)

        albums.extend(raw['items']) # limit default 값이 20이므로 20개씩 추가된다.
        print(albums)

    print(len(albums))
    sys.exit(0)


# Have your application request authorization (get access_token)
def get_headers(client_id, client_secret):

    endpoint = "https://accounts.spotify.com/api/token"
    encoded = base64.b64encode("{}:{}".format(client_id, client_secret).encode('utf-8')).decode('ascii')

    headers = {
        "Authorization": "Basic {}".format(encoded)
    }

    payload = {
        "grant_type": "client_credentials"
    }

    r = requests.post(endpoint, data=payload, headers=headers)

    access_token = json.loads(r.text)['access_token']

    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    return headers


if __name__=='__main__':
    main()