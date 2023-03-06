from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from generate_playlist import get_playlist
import json
import numpy as np

app = Flask(__name__)
CORS(app, origins=['www.untz.studio',
                    'untz-vivid.vercel.app',
                    'untz-vivid-adamziff.vercel.app', 
                    'http://localhost:3000'])
# CORS(app)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({ 'data': 'Hello, World!' })

@app.route('/api/generate-playlist', methods=['GET'])
def generate_playlist():
    users = request.args.get('users')
    users = json.loads(users)
    energy_curve = request.args.get('energy_curve')
    energy_curve = json.loads(energy_curve)
    print('energy_curve:', energy_curve)

    if request.args.get('must_plays') is not None:
        must_plays = request.args.get('must_plays')
        must_plays = json.loads(must_plays)
    else:
        must_plays = []
    if request.args.get('do_not_plays') is not None:
        do_not_plays = request.args.get('do_not_plays')
        do_not_plays = json.loads(do_not_plays)
    else:
        do_not_plays = []
    if request.args.get('chaos') is not None:
        NUM_RECOMMENDATIONS = int(request.args.get('chaos'))
    else:
        NUM_RECOMMENDATIONS = 100
    if request.args.get('artist_penalty') is not None:
        ARTIST_PENALTY = int(request.args.get('artist_penalty'))
    else:
        ARTIST_PENALTY = 0.05
    if request.args.get('chosen_features_weight') is not None:
        CHOSEN_FEATURES_WEIGHT = int(request.args.get('chosen_features_weight'))
    else:
        CHOSEN_FEATURES_WEIGHT = 100
    if request.args.get('num_songs_to_select') is not None:
        NUM_SONGS_TO_SELECT = int(request.args.get('num_songs_to_select')) - len(must_plays)
    else:
        NUM_SONGS_TO_SELECT = 30
    
    
    try:
        tracks = get_playlist(users, must_plays, do_not_plays, energy_curve, NUM_RECOMMENDATIONS, ARTIST_PENALTY, CHOSEN_FEATURES_WEIGHT, NUM_SONGS_TO_SELECT)
        response_data = {'tracks': tracks}
        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        response_data = {'error': error_msg}
        response = make_response(jsonify(response_data), 500)
        response.headers['Content-Type'] = 'application/json'
        return response