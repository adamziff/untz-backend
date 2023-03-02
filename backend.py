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
    try:
        tracks = get_playlist(users)
        response_data = {'tracks': tracks.to_dict()}
        response = make_response(jsonify(response_data), 200)
        response.headers['Content-Type'] = 'application/json'
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