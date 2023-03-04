from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from generate_playlist import get_playlist
import json

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
    print('users:', users)
    energy_curve = request.args.get('energy_curve')
    energy_curve = json.loads(energy_curve)
    print('energy_curve:', energy_curve)

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
        NUM_SONGS_TO_SELECT = int(request.args.get('num_songs_to_select'))
    else:
        NUM_SONGS_TO_SELECT = 30
    
    try:
        tracks = get_playlist(users, energy_curve, NUM_RECOMMENDATIONS, ARTIST_PENALTY, CHOSEN_FEATURES_WEIGHT, NUM_SONGS_TO_SELECT)
        response_data = {'tracks': tracks}
        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json'

        # add playlist to spotify
        return response
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        response_data = {'error': error_msg}
        response = make_response(jsonify(response_data), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

# def generate_playlist():
#     # users = request.args.getlist('users')
#     # print('users:', users)
#     # print('request.args:', request.args)
#     # tracks = get_playlist(users)
#     # return jsonify({'tracks': tracks})

#     users = request.args.get('users')
#     users = json.loads(users)
#     print('users:', users)
#     tracks = get_playlist(users)
#     return jsonify({'tracks': tracks.to_dict()})