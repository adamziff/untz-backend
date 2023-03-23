from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from generate_playlist import get_playlist, print_tracks
import json
import numpy as np

app = Flask(__name__)
cors_origins = ['www.untz.studio',
                'https://www.untz.studio',
                'https://untz-vivid.vercel.app',
                'https://untz-vivid-adamziff.vercel.app', 
                'http://localhost:3000']
CORS(app, resources={r"/*": {"origins": cors_origins, "methods": ["GET", "POST", "OPTIONS"]}})

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in cors_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({ 'data': 'Hello, World!' })

@app.route('/api/generate-playlist', methods=['GET'])
def generate_playlist():
    print('generate playlist called')
    users = request.args.get('users')
    users = json.loads(users)
    print('users')
    print(users)
    print()

    # Iterate through the 2D array and ensure each string begins with "spotify:track:"
    for user in users:
        for i in range(len(user)):
            if not user[i].startswith("spotify:track:"):
                user[i] = "spotify:track:" + user[i]

    energy_curve = request.args.get('energy_curve')
    energy_curve = json.loads(energy_curve)
    print('energy_curve:', energy_curve)

    if request.args.get('must_plays') is not None:
        must_plays = request.args.get('must_plays')
        must_plays = json.loads(must_plays)
        # Iterate through the array and ensure each string begins with "spotify:track:"
        for i in range(len(must_plays)):
            if not must_plays[i].startswith("spotify:track:"):
                must_plays[i] = "spotify:track:" + must_plays[i]
    else:
        must_plays = []
    if request.args.get('do_not_plays') is not None:
        do_not_plays = request.args.get('do_not_plays')
        # do_not_plays = do_not_plays.replace("%27", "%22") # Replace single quotes with double quotes
        do_not_plays = json.loads(do_not_plays)
        # Iterate through the array and ensure each string begins with "spotify:track:"
        for i in range(len(do_not_plays)):
            if not do_not_plays[i].startswith("spotify:track:"):
                do_not_plays[i] = "spotify:track:" + do_not_plays[i]
    else:
        do_not_plays = []
    if request.args.get('chaos') is not None:
        NUM_RECOMMENDATIONS = int(request.args.get('chaos'))
        CHOSEN_FEATURES_WEIGHT = 101-int(request.args.get('chaos'))
    else:
        NUM_RECOMMENDATIONS = 100
        CHOSEN_FEATURES_WEIGHT = 100
    if request.args.get('artist_penalty') is not None:
        ARTIST_PENALTY = int(request.args.get('artist_penalty'))
    else:
        ARTIST_PENALTY = 0.05
    if request.args.get('num_songs_to_select') is not None:
        NUM_SONGS_TO_SELECT = int(request.args.get('num_songs_to_select')) - len(must_plays)
    else:
        NUM_SONGS_TO_SELECT = 30

    while NUM_RECOMMENDATIONS * len(users) <= NUM_SONGS_TO_SELECT and NUM_RECOMMENDATIONS < 100:
        NUM_RECOMMENDATIONS += 1

    print('parameters set')
    
    while True:
        try:
            print('calling get_playlist')
            tracks = get_playlist(users, must_plays, do_not_plays, energy_curve, NUM_RECOMMENDATIONS, ARTIST_PENALTY, CHOSEN_FEATURES_WEIGHT, NUM_SONGS_TO_SELECT)
            print('get_playlist returned, tracks:')
            print(tracks)
            not_found = set(must_plays) - set(tracks)

            if not_found:
                print("The following songs were not found in the tracks list:")
                for song in not_found:
                    print(song)
            else:
                print("All songs in must_plays were found in the tracks list.")

            response_data = {'tracks': tracks}
            response = make_response(jsonify(response_data), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        except Exception as e:
            print('e')
            print(e)
            if (e.response and e.response.status_code and hasattr(e, 'response') and e.response.status_code == 443) or e.port == 443:
                # The Spotify API timed out, retrying...
                print('The Spotify API timed out, retrying...')
                continue
            else:
                print(e.port)
                print(e.host)
                print(e.response.port)
                error_msg = f"An error occurred: {str(e)}"
                response_data = {'error': error_msg}
                response = make_response(jsonify(response_data), 500)
                response.headers['Content-Type'] = 'application/json'
                return response
            