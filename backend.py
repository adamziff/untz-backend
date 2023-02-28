from flask import Flask, jsonify, request
from flask_cors import CORS
from generate_playlist import get_playlist
import json

app = Flask(__name__)
# CORS(app, origins=['https://untzdj.azurewebsites.net/', 'http://localhost:3000'])
CORS(app)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({ 'data': 'Hello, World!' })

@app.route('/api/generate-playlist', methods=['GET'])
def generate_playlist():
    # users = request.args.getlist('users')
    # print('users:', users)
    # print('request.args:', request.args)
    # tracks = get_playlist(users)
    # return jsonify({'tracks': tracks})

    users = request.args.get('users')
    users = json.loads(users)
    print('users:', users)
    tracks = get_playlist(users)
    return jsonify({'tracks': tracks.to_dict()})