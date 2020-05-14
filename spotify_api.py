import sys
import requests
import base64
import json
import logging

client_id = "8d0c1ff1b39046a5bac58c0d81709a02"
client_secret = "8d0c1ff1b39046a5bac58c0d81709a02"

def main():

    endpoint = "https://accounts.spotify.com/api/token"

    encoded = base64.b64encode("{}:{}".format(client_id, client_secret).encode('utf-8')).decode('ascii')

    headers = {
        "Authorization": "Basic {}".format(encoded)
    }

if __name__=='__main__':
    main()