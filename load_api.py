from flask import Flask, request, jsonify, render_template_string
from functools import wraps
from datetime import datetime
import json
import os
from collections import Counter

app = Flask(__name__)

#  API Key
API_KEY = "ghEkud182u19"
LOG_FILE = "call_reports.jsonl"

# Decorator for API key authentication
def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get("x-api-key") == API_KEY:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 401
    return decorated_function

mock_loads = [
    {
        "load_id": "LD1001",
        "origin": "Chicago, IL",
        "destination": "Dallas, TX",
        "pickup_datetime": "2025-11-29T08:15:30-05:00",
        "delivery_datetime": "2025-12-05T09:05:30-05:00",
        "equipment_type": "Dry Van",
        "loadboard_rate": 2200.00,
        "notes": "No touch freight",
        "weight": "42000 lbs",
        "commodity_type": "Consumer Goods",
        "num_of_pieces": 26,
        "miles": 980,
        "dimensions": "48ft x 102in"
    },
    {
        "load_id": "LD1002",
        "origin": "Atlanta, GA",
        "destination": "Orlando, FL",
        "pickup_datetime": "2025-08-05T09:00:00Z",
        "delivery_datetime": "2025-08-06T16:00:00Z",
        "equipment_type": "Reefer",
        "loadboard_rate": 1500.00,
        "notes": "Must maintain 36°F",
        "weight": "38000 lbs",
        "commodity_type": "Perishables",
        "num_of_pieces": 20,
        "miles": 440,
        "dimensions": "53ft x 102in"
    },
    {
        "load_id": "LD1003",
        "origin": "Los Angeles, CA",
        "destination": "Phoenix, AZ",
        "pickup_datetime": "2025-09-10T07:30:00-07:00",
        "delivery_datetime": "2025-09-11T13:00:00-07:00",
        "equipment_type": "Flatbed",
        "loadboard_rate": 1800.00,
        "notes": "Straps required",
        "weight": "46000 lbs",
        "commodity_type": "Steel Coils",
        "num_of_pieces": 15,
        "miles": 370,
        "dimensions": "48ft x 102in"
    },
    {
        "load_id": "LD1004",
        "origin": "Seattle, WA",
        "destination": "Boise, ID",
        "pickup_datetime": "2025-10-01T08:00:00-07:00",
        "delivery_datetime": "2025-10-02T17:00:00-07:00",
        "equipment_type": "Dry Van",
        "loadboard_rate": 1700.00,
        "notes": "Live unload",
        "weight": "41000 lbs",
        "commodity_type": "Office Supplies",
        "num_of_pieces": 30,
        "miles": 500,
        "dimensions": "53ft x 102in"
    },
    {
        "load_id": "LD1005",
        "origin": "Denver, CO",
        "destination": "Salt Lake City, UT",
        "pickup_datetime": "2025-09-15T10:00:00-06:00",
        "delivery_datetime": "2025-09-16T15:00:00-06:00",
        "equipment_type": "Reefer",
        "loadboard_rate": 1900.00,
        "notes": "Frozen goods -20°F",
        "weight": "40000 lbs",
        "commodity_type": "Frozen Meat",
        "num_of_pieces": 18,
        "miles": 520,
        "dimensions": "53ft x 102in"
    }
]


# API Endpoint
@app.route("/loads", methods=["GET"])
@require_api_key
def get_loads():
    origin = request.args.get("origin", "").strip().lower()
    equipment_type = request.args.get("equipment_type", "").strip().lower()
    pickup_datetime = request.args.get("pickup_datetime", "").strip()
    destination = request.args.get("destination", "").strip().lower()

    def parse_datetime(dt):
        try:
            return datetime.fromisoformat(dt)
        except Exception:
            return None

    def extract_state(location):
        parts = location.split(',')
        return parts[-1].strip().lower() if len(parts) > 1 else ""

    def score(load):
        score = 0
        if origin and origin == load["origin"].strip().lower():
            score += 5
        elif origin and extract_state(origin) == extract_state(load["origin"]):
            score += 2

        if destination and destination == load["destination"].strip().lower():
            score += 5
        elif destination and extract_state(destination) == extract_state(load["destination"]):
            score += 2

        if equipment_type and equipment_type == load["equipment_type"].strip().lower():
            score += 10

        if pickup_datetime:
            requested = parse_datetime(pickup_datetime)
            actual = parse_datetime(load["pickup_datetime"])
            if requested and actual:
                diff = abs((requested - actual).total_seconds())
                score += max(0, 5 - diff / 3600)  # up to 5 points if within 1 hour

        return score

    ranked = sorted(mock_loads, key=score, reverse=True)
    return jsonify({"data": ranked[:1] if ranked else []})

# Report Receiving Endpoint
@app.route("/report", methods=["POST"])
@require_api_key
def receive_report():
    try:
        data = request.get_json(force=True)
        data["received_at"] = datetime.utcnow().isoformat()
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# Dashboard Endpoint
@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        if not os.path.exists(LOG_FILE):
            return "No reports available."

        with open(LOG_FILE, "r") as f:
            records = [json.loads(line) for line in f if line.strip()]

        total_calls = len(records)
        deals_closed = sum(1 for r in records if r.get("negotiation_result") == "accepted")
        avg_rate_diff = round(
            sum(r.get("loadboard_rate", 0) - r.get("agreed_rate", 0) for r in records if r.get("negotiation_result") == "accepted") / max(deals_closed, 1),
            2
        )
        avg_call_length = round(
            sum(r.get("call_duration_sec", 0) for r in records) / max(total_calls, 1), 2
        )
        deal_rate = round(deals_closed / total_calls * 100, 2) if total_calls else 0

        accepted = [r for r in records if r.get("negotiation_result") == "accepted"]
        chart_labels = [f"{r.get('origin', '?')}→{r.get('destination', '?')}" for r in accepted]
        loadboard_rates = [r.get("loadboard_rate", 0) for r in accepted]
        agreed_rates = [r.get("agreed_rate", 0) for r in accepted]

        # Equipment frequency chart data
        equipment_counter = Counter(r.get("equipment_type", "Unknown") for r in records)
        equipment_labels = list(equipment_counter.keys())
        equipment_counts = list(equipment_counter.values())

        html = f"""
        <html>
        <head>
            <title>📊 HappyRobot Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Roboto', sans-serif; padding: 20px; background: #f5f5f5; }}
                h1 {{ color: #333; }}
                .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
                canvas {{ max-width: 100%; }}
            </style>
        </head>
        <body>
            <h1>📊 HappyRobot Call Report Dashboard</h1>
            <div class="card">
                <h3>Summary Metrics</h3>
                <p><strong>Total Calls:</strong> {total_calls}</p>
                <p><strong>Deals Closed:</strong> {deals_closed}</p>
                <p><strong>Deal Rate:</strong> {deal_rate}%</p>
                <p><strong>Average Rate Difference:</strong> ${avg_rate_diff}</p>
                <p><strong>Average Call Length:</strong> {avg_call_length} sec</p>
            </div>
            <div class="card">
                <h3>Rate Comparison for Accepted Deals</h3>
                <canvas id="rateChart"></canvas>
            </div>
            <div class="card">
                <h3>Most Frequent Equipment Types</h3>
                <canvas id="equipmentChart"></canvas>
            </div>
            <script>
                const ctx = document.getElementById('rateChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {chart_labels},
                        datasets: [
                            {{ label: 'Loadboard Rate', data: {loadboard_rates}, backgroundColor: 'rgba(54, 162, 235, 0.6)' }},
                            {{ label: 'Agreed Rate', data: {agreed_rates}, backgroundColor: 'rgba(75, 192, 192, 0.6)' }}
                        ]
                    }},
                    options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
                }});

                const eqCtx = document.getElementById('equipmentChart').getContext('2d');
                new Chart(eqCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {equipment_labels},
                        datasets: [
                            {{ label: 'Equipment Type Frequency', data: {equipment_counts}, backgroundColor: 'rgba(153, 102, 255, 0.6)' }}
                        ]
                    }},
                    options: {{ responsive: true, scales: {{ y: {{ beginAtZero: true }} }} }}
                }});
            </script>
        </body>
        </html>
        """
        return render_template_string(html)
    except Exception as e:
        return f"Error loading dashboard: {str(e)}"

# 🚀 Run the API
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
