from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
import urllib.parse
import sys

# Initialize the Flask application
app = Flask(__name__)

def get_mongo_client():
    """
    Constructs and returns a MongoClient with support for:
    1. Direct MONGODB_URI environment variable (if specified)
    2. Explicit credentials (MONGO_USERNAME, MONGO_PASSWORD, MONGO_HOST, MONGO_PORT, MONGO_DATABASE)
    3. Unauthenticated fallback (mongodb://localhost:27017/) for simple local dev
    """
    direct_uri = os.environ.get("MONGODB_URI")
    if direct_uri:
        mongo_uri = direct_uri
    else:
        user = os.environ.get("MONGO_USERNAME") or os.environ.get("MONGO_INITDB_ROOT_USERNAME")
        password = os.environ.get("MONGO_PASSWORD") or os.environ.get("MONGO_INITDB_ROOT_PASSWORD")
        host = os.environ.get("MONGO_HOST", "localhost")
        port = os.environ.get("MONGO_PORT", "27017")
        database = os.environ.get("MONGO_DATABASE") or os.environ.get("MONGO_DB", "flask_db")
        auth_source = os.environ.get("MONGO_AUTH_SOURCE", "admin")

        if user and password:
            encoded_user = urllib.parse.quote_plus(user)
            encoded_pass = urllib.parse.quote_plus(password)
            mongo_uri = f"mongodb://{encoded_user}:{encoded_pass}@{host}:{port}/{database}?authSource={auth_source}"
        else:
            mongo_uri = f"mongodb://{host}:{port}/{database}"

    print(f"Connecting to MongoDB at: {mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri}", file=sys.stderr)
    return MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

# Set up the MongoDB client and select database and collection
client = get_mongo_client()
db_name = os.environ.get("MONGO_DATABASE") or os.environ.get("MONGO_DB", "flask_db")
db = client[db_name]
collection = db.data

# Define the route for the root URL
@app.route('/', methods=['GET'])
def index():
    # Return a welcome message with the current time
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"

# Define the route for the '/data' endpoint
# This endpoint supports both GET and POST methods
@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        # Retrieve JSON payload from incoming request
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({"error": "Invalid JSON payload provided"}), 400
        
        # Insert data into the 'data' collection in MongoDB
        collection.insert_one(payload)
        return jsonify({"status": "Data inserted"}), 201

    elif request.method == 'GET':
        # Retrieve all documents excluding the MongoDB '_id' field
        data_records = list(collection.find({}, {"_id": 0}))
        return jsonify(data_records), 200

# Health check endpoint for Docker & Kubernetes liveness/readiness probes
@app.route('/healthz', methods=['GET'])
def health():
    try:
        # Ping the MongoDB server to verify connectivity
        client.admin.command('ping')
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc)
        }), 503

# Run the Flask application
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug_mode = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host=host, port=port, debug=debug_mode)
