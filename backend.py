from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
# CORS(app, origins=['http://localhost:3000'])
# CORS(app, origins=['https://untzdj.azurewebsites.net/'])
# CORS(app, origins=['https://untzdj.azurewebsites.net/', 'http://localhost:3000'])
CORS(app)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({ 'data': 'Hello, World!' })