from flask import Flask, request
from lib import math

app = Flask(__name__)

@app.route('/add', methods=['GET'])
def add_numbers():
    a = int(request.args.get('a', 0))
    b = int(request.args.get('b', 0))
    result = math.add(a, b)
    return f"Result: {result}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)  # Listen on all interfaces, port 8080
