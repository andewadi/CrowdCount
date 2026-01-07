from flask import Flask, jsonify, render_template, request, session
import json
import os
import csv
from flask import send_file

#PATHS
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DATA_FILE = os.path.join(PROJECT_ROOT, "live_data.json")

#FLASK APP
app = Flask(
    __name__,
    template_folder=os.path.join(BACKEND_DIR, "templates"),
    static_folder=os.path.join(BACKEND_DIR, "static")
)

app.secret_key = "crowdcount-secret-key"

#USERS
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

#ROUTES
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = USERS.get(data.get("username"))

    if not user or user["password"] != data.get("password"):
        return jsonify({"error": "Invalid credentials"}), 401

    session["username"] = data["username"]
    session["role"] = user["role"]

    return jsonify({"role": user["role"]})

@app.route("/get_count", methods=["GET"])
def get_count():
    if "role" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if not os.path.exists(DATA_FILE):
        return jsonify({
            "total_live": 0,
            "total_cumulative": 0,
            "zones": {},
            "timestamp": "--:--:--"
        })

    with open(DATA_FILE, "r") as f:
        return jsonify(json.load(f))

@app.route("/download_logs")
def download_logs():
    if session.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403

    if not os.path.exists(DATA_FILE):
        return jsonify({"error": "No data file"}), 404

    csv_path = os.path.join(PROJECT_ROOT, "crowd_logs.csv")

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Zone", "Live Count", "Total Count"])

        for zone, values in data["zones"].items():
            writer.writerow([
                data["timestamp"],
                zone,
                values["live"],
                values["total"]
            ])

    return send_file(csv_path, as_attachment=True)

#MAIN
if __name__ == "__main__":
    print("🚀 Flask running at http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=8000, debug=True, use_reloader=False)
