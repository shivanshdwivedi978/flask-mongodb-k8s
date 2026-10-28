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

def render_dashboard(now):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flask & MongoDB Application Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: rgba(22, 30, 49, 0.75);
      --border: rgba(148, 163, 184, 0.15);
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --success: #10b981;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: radial-gradient(circle at 10% 20%, #172554, #0b0f19 80%);
      color: var(--text);
      min-height: 100vh;
      padding: 2.5rem 1rem;
    }}
    .container {{ max-width: 960px; margin: 0 auto; }}
    .card {{
      background: var(--card-bg);
      backdrop-filter: blur(16px);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.75rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 15px 30px -10px rgba(0, 0, 0, 0.4);
    }}
    .header-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 500;
      margin-bottom: 0.85rem;
    }}
    .header-badge span.dot {{
      width: 8px; height: 8px; border-radius: 50%; background: #34d399; display: inline-block;
      box-shadow: 0 0 8px #34d399;
    }}
    h1 {{
      font-size: 1.6rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      color: #ffffff;
    }}
    .time-banner {{
      font-family: 'JetBrains Mono', monospace;
      color: var(--primary);
      background: rgba(56, 189, 248, 0.08);
      border-left: 3px solid var(--primary);
      padding: 0.85rem 1rem;
      border-radius: 4px 8px 8px 4px;
      margin-top: 1rem;
      font-size: 0.95rem;
    }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
    @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    label {{ display: block; font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem; font-weight: 500; }}
    textarea {{
      width: 100%;
      background: #060911;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem;
      color: #38bdf8;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      outline: none;
      height: 120px;
      resize: vertical;
      transition: border-color 0.2s;
    }}
    textarea:focus {{ border-color: var(--primary); }}
    button {{
      background: var(--primary);
      color: #0b0f19;
      border: none;
      font-weight: 600;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    button:hover {{ background: var(--primary-hover); transform: translateY(-1px); }}
    .status-msg {{ margin-top: 0.75rem; font-size: 0.85rem; }}
    .nav-links {{ display: flex; gap: 1.25rem; margin-top: 1.25rem; font-size: 0.85rem; }}
    .nav-link {{ color: var(--primary); text-decoration: none; display: inline-flex; align-items: center; gap: 4px; }}
    .nav-link:hover {{ text-decoration: underline; }}
    pre {{ font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="header-badge"><span class="dot"></span> MongoDB Connected & Authenticated</div>
      <h1>Welcome to the Flask app!</h1>
      <div class="time-banner">The current time is: {now}</div>
      <div class="nav-links">
        <a href="/data" target="_blank" class="nav-link">↗ View Raw JSON (/data)</a>
        <a href="/healthz" target="_blank" class="nav-link">↗ Health Check (/healthz)</a>
      </div>
    </div>

    <div class="grid">
      <!-- Data Insert Section -->
      <div class="card">
        <h2 style="font-size: 1.15rem; margin-bottom: 0.75rem;">➕ Insert Data into MongoDB</h2>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
          Sends a <code>POST /data</code> request storing the JSON in the authenticated MongoDB collection.
        </p>
        <form id="insertForm">
          <div style="margin-bottom: 1rem;">
            <label for="jsonInput">JSON Payload:</label>
            <textarea id="jsonInput">{{\n  "candidate": "Shivansh Dwivedi",\n  "project": "flask-mongodb-k8s",\n  "status": "active"\n}}</textarea>
          </div>
          <button type="submit" id="submitBtn">Insert Document</button>
          <div id="statusMsg" class="status-msg"></div>
        </form>
      </div>

      <!-- Live Records List -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <h2 style="font-size: 1.15rem;">📊 Stored Records (GET /data)</h2>
          <button type="button" onclick="loadData()" style="padding: 4px 10px; font-size: 0.8rem;">↻ Refresh</button>
        </div>
        <div id="recordsContainer" style="margin-top: 1rem; max-height: 280px; overflow-y: auto;">
          <p style="color: var(--text-muted); font-size: 0.85rem;">Loading documents from MongoDB...</p>
        </div>
      </div>
    </div>
  </div>

  <script>
    async function loadData() {{
      const container = document.getElementById('recordsContainer');
      try {{
        const res = await fetch('/data');
        const data = await res.json();
        if (!data || data.length === 0) {{
          container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No documents in MongoDB yet. Insert one on the left!</p>';
          return;
        }}
        let html = '<div style="display:flex; flex-direction:column; gap:0.5rem;">';
        data.forEach((doc, idx) => {{
          html += `<div style="background:#060911; padding:0.6rem 0.8rem; border-radius:6px; border:1px solid var(--border);">
            <div style="font-size:0.75rem; color:var(--primary); margin-bottom:0.25rem;">Record #${{idx + 1}}</div>
            <pre style="color:#e2e8f0; margin:0;">${{JSON.stringify(doc, null, 2)}}</pre>
          </div>`;
        }});
        html += '</div>';
        container.innerHTML = html;
      }} catch (err) {{
        container.innerHTML = `<p style="color:#ef4444; font-size:0.85rem;">Failed to load data: ${{err.message}}</p>`;
      }}
    }}

    document.getElementById('insertForm').addEventListener('submit', async (e) => {{
      e.preventDefault();
      const status = document.getElementById('statusMsg');
      const input = document.getElementById('jsonInput').value;
      let parsed;
      try {{
        parsed = JSON.parse(input);
      }} catch(err) {{
        status.innerHTML = `<span style="color:#ef4444;">❌ Invalid JSON: ${{err.message}}</span>`;
        return;
      }}

      try {{
        status.innerHTML = '<span style="color:var(--text-muted);">Inserting...</span>';
        const res = await fetch('/data', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(parsed)
        }});
        if (res.status === 201) {{
          status.innerHTML = '<span style="color:#10b981;">✅ Document successfully inserted into MongoDB!</span>';
          loadData();
        }} else {{
          const errData = await res.json();
          status.innerHTML = `<span style="color:#ef4444;">❌ Error ${{res.status}}: ${{errData.error || 'Failed'}}</span>`;
        }}
      }} catch (err) {{
        status.innerHTML = `<span style="color:#ef4444;">❌ Request failed: ${{err.message}}</span>`;
      }}
    }});

    loadData();
  </script>
</body>
</html>
"""

# Define the route for the root URL
@app.route('/', methods=['GET'])
def index():
    now = datetime.now()
    accept_header = request.headers.get('Accept', '')
    user_agent = request.headers.get('User-Agent', '').lower()

    # If accessed from a web browser (HTML client), provide the interactive UI
    if 'text/html' in accept_header and 'curl' not in user_agent:
        return render_dashboard(now)

    # Return standard plain-text welcome message for CLI / curl / automated tests
    return f"Welcome to the Flask app! The current time is: {now}"

# Dedicated route that always serves the interactive UI
@app.route('/ui', methods=['GET'])
def ui():
    return render_dashboard(datetime.now())

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
