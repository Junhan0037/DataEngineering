import sys
import logging
import boto3
import requests
import base64
import json
import pymysql
from datetime import datetime
import pandas as pd
import jsonpath  # pip3 install jsonpath --user

client_id = "" # Client ID
client_secret = "" # Client Secret

host = ""
port = 3306
username = "junhan"
database = ""
password = ""

def main():

    # RDS 연결.
    try:
        conn = pymysql.connect(host, user=username, passwd=password, db=database, port=port, use_unicode=True, charset='utf8')
        cursor = conn.cursor()
    except:
        logging.error("could not connect to rds")
        sys.exit(1)

    headers = get_headers(client_id, client_secret)

    # RDS - 아티스트 ID 추출.
    cursor.execute("SELECT id FROM artists")

    top_track_keys = {
        "id": "id",
        "name": "name",
        "popularity": "popularity",
        "external_url": "external_urls.spotify"
    }

    # Top Tracks Spotify 가져오고
    top_tracks = []
    for (id, ) in cursor.fetchall():

        URL = "https://api.spotify.com/v1/artists/{}/top-tracks".format(id)
        params = {
            'country': 'US'
        }
        r = requests.get(URL, params=params, headers=headers)
        raw = json.loads(r.text)

        for i in raw['tracks']:
            top_track = {}
            for key, value in top_track_keys.items():
                top_track.update({key: jsonpath.jsonpath(i, value)}) # jsonpath를 통해 value값을 찾는다.
                top_track.update({'artist_id': id})
                top_tracks.append(top_track)

    # track_ids
    track_ids = [i['id'][0] for i in top_tracks]

    # list of dictionariescls
    top_tracks = pd.DataFrame(top_tracks)
    top_tracks.to_parquet('top-tracks.parquet', engine='pyarrow', compression='snappy') # Spark에 적합한 parquet형식으로 변형.

    dt = datetime.utcnow().strftime("%Y-%m-%d")

    # S3 import
    s3 = boto3.resource('s3')
    object = s3.Object('fastcampus-spotify', 'top-tracks/dt={}/top-tracks.parquet'.format(dt))
    data = open('top-tracks.parquet', 'rb')
    object.put(Body=data)

    # batch 형식
    tracks_batch = [track_ids[i: i+100] for i in range(0, len(track_ids), 100)]

    audio_features = []
    for i in tracks_batch:
        ids = ','.join(i)
        URL = "https://api.spotify.com/v1/audio-features/?ids={}".format(ids)

        r = requests.get(URL, headers=headers)
        raw = json.loads(r.text)

        audio_features.extend(raw['audio_features'])

    audio_features = pd.DataFrame(audio_features)
    audio_features.to_parquet('audio-features.parquet', engine='pyarrow', compression='snappy')

    # S3 import
    s3 = boto3.resource('s3')
    object = s3.Object('fastcampus-spotify', 'audio-features/dt={}/audio-features.parquet'.format(dt))
    data = open('audio-features.parquet', 'rb')
    object.put(Body=data)

    # artists.parquet
    cursor.execute("SELECT * FROM artists")
    colnames = [d[0] for d in cursor.description]
    artists = [dict(zip(colnames, row)) for row in cursor.fetchall()]
    artists = pd.DataFrame(artists)

    artists.to_parquet('artists.parquet', engine='pyarrow', compression='snappy')

    # S3 import
    s3 = boto3.resource('s3')
    object = s3.Object('fastcampus-spotify', 'artists/dt={}/artists.parquet'.format(dt))
    data = open('artists.parquet', 'rb')
    object.put(Body=data)

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


if __name__ == '__main__':
    main()