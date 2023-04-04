from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from generate_playlist import get_playlist, print_tracks
import json
from pymongo import MongoClient, errors as pymongo_errors
import os

app = Flask(__name__)
cors_origins = ['www.untz.studio',
                'https://www.untz.studio',
                'https://untz-vivid.vercel.app',
                'https://untz-vivid-adamziff.vercel.app', 
                'http://localhost:3000']
CORS(app, resources={r"/*": {"origins": cors_origins, "methods": ["GET", "POST", "OPTIONS"]}})

mongodb_uri = os.environ.get('MONGODB_URI')

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in cors_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        # response.headers.add('Vary', 'Origin')
    return response

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({ 'data': 'Hello, World!' })

@app.route('/api/generate-playlist', methods=['GET'])
def generate_playlist():
    print('generate playlist called')
    access_code = request.args.get('accessCode')
    # access_code = json.loads(access_code)

    client = MongoClient(mongodb_uri)
    db = client["untz-db"]
    parties_collection = db["parties"]
    party = parties_collection.find_one({"access_code": access_code})
    print('party')
    print(party)
    print()
    print(party['name'])
    print()

    duration = party['duration']
    energy_curve = party['energy_curve']
    chaos = party['chaos']
    users = party['requests']
    must_plays = party['mustPlays']
    do_not_plays = party['doNotPlays']

    # Iterate through the 2D array and ensure each string begins with "spotify:track:"
    for user in users:
        for i in range(len(user)):
            if not user[i].startswith("spotify:track:"):
                user[i] = "spotify:track:" + user[i]

    print('energy_curve:', energy_curve)

    if must_plays is not None:
        # Iterate through the array and ensure each string begins with "spotify:track:"
        for i in range(len(must_plays)):
            if not must_plays[i].startswith("spotify:track:"):
                must_plays[i] = "spotify:track:" + must_plays[i]
    else:
        must_plays = []
    if do_not_plays is not None:
        # Iterate through the array and ensure each string begins with "spotify:track:"
        for i in range(len(do_not_plays)):
            if not do_not_plays[i].startswith("spotify:track:"):
                do_not_plays[i] = "spotify:track:" + do_not_plays[i]
    else:
        do_not_plays = []
    if chaos is not None:
        NUM_RECOMMENDATIONS = int(chaos)
        CHOSEN_FEATURES_WEIGHT = 101-int(chaos)
    else:
        NUM_RECOMMENDATIONS = 100
        CHOSEN_FEATURES_WEIGHT = 100
    # if request.args.get('artist_penalty') is not None:
    #     ARTIST_PENALTY = int(request.args.get('artist_penalty'))
    # else:
    ARTIST_PENALTY = 0.05
    if duration is not None:
        NUM_SONGS_TO_SELECT = int(duration/3) - len(must_plays)
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
            # if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 443:
            if "Read timed out" in str(e):
                # The Spotify API timed out, retrying...
                print('The Spotify API timed out, retrying...')
                print()
                continue
            else:
                error_msg = f"An error occurred: {str(e)}"
                response_data = {'error': error_msg}
                response = make_response(jsonify(response_data), 500)
                response.headers['Content-Type'] = 'application/json'
                return response
            