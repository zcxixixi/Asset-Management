from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/api/data')
def get_data():
    try:
        with open('src/data.json') as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({"error": "No data"})

if __name__ == '__main__':
    app.run(port=5000)
