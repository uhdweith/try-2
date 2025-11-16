import os
import json
import random
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# ============================
# CONFIG (environment variables in Render)
# ============================
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
LOCATION = "Bengaluru"

# ============================
# HEALTH DATA GENERATOR
# ============================
def generate_health_data(posted_data=None):
    """Generate simulated wellness data OR use POSTed JSON values."""
    if posted_data:
        # Use POSTed values (ReqBin), fallback to random if missing
        data = {
            "continuous_heart_rate": posted_data.get("continuous_heart_rate", random.randint(60, 100)),
            "sleep_duration_hours": posted_data.get("sleep_duration_hours", round(random.uniform(5, 9), 1)),
            "sleep_quality": posted_data.get("sleep_quality", random.choice(["Poor", "Average", "Good", "Excellent"])),
            "bedtime_consistency": posted_data.get("bedtime_consistency", random.choice(["Irregular", "Moderate", "Consistent"])),
            "spo2": posted_data.get("spo2", random.randint(94, 100)),
            "body_temperature_c": posted_data.get("body_temperature_c", round(random.uniform(36.2, 37.5), 1)),
            "steps": posted_data.get("steps", random.randint(2000, 12000)),
            "distance_km": posted_data.get("distance_km", round(random.uniform(1.0, 8.0), 1)),
            "calories_burned": posted_data.get("calories_burned", random.randint(1500, 3000))
        }
    else:
        # GET request = full random simulation
        data = {
            "continuous_heart_rate": random.randint(60, 100),
            "sleep_duration_hours": round(random.uniform(5, 9), 1),
            "sleep_quality": random.choice(["Poor", "Average", "Good", "Excellent"]),
            "bedtime_consistency": random.choice(["Irregular", "Moderate", "Consistent"]),
            "spo2": random.randint(94, 100),
            "body_temperature_c": round(random.uniform(36.2, 37.5), 1),
            "steps": random.randint(2000, 12000),
            "distance_km": round(random.uniform(1.0, 8.0), 1),
            "calories_burned": random.randint(1500, 3000)
        }

    return data

# ============================
# WEATHER FETCH
# ============================
def get_weather():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            return {
                "weather": data["weather"][0]["description"],
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"]
            }
        else:
            return {
                "error": f"Weather API failed: {data.get('message', 'unknown error')}"
            }
    except Exception as e:
        return {"error": f"Weather error: {str(e)}"}

# ============================
# AI INSIGHT + STATE (1/2/3)
# ============================
def get_ai_insight_and_state(health_data, weather_data):
    try:
        # The prompt instructs DeepSeek to return ONLY JSON with insight + state
        prompt = f"""
        Return ONLY a JSON object with this format:

        {{
            "insight": "<one short actionable wellness sentence>",
            "state": <number from 1 to 3>
        }}

        Where:
        1 = poor wellness
        2 = average wellness
        3 = good wellness

        DO NOT return anything else. DO NOT add text outside the JSON.

        Health Data:
        {json.dumps(health_data)}

        Weather Data:
        {json.dumps(weather_data)}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Return JSON only."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        ai_raw = response.json()["choices"][0]["message"]["content"]

        # Parse AI JSON safely
        try:
            ai_json = json.loads(ai_raw)
            insight = ai_json.get("insight", "Stay mindful and hydrated.")
            state = int(ai_json.get("state", 2))
        except:
            insight = "Stay mindful and hydrated."
            state = 2  # fallback

        return insight, state

    except Exception as e:
        return ("AI unavailable — maintain good habits.", 2)

# ============================
# MAIN ROUTE (GET + POST)
# ============================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        posted_data = request.get_json()
    else:
        posted_data = None

    health_data = generate_health_data(posted_data)
    weather_data = get_weather()
    insight, state = get_ai_insight_and_state(health_data, weather_data)

    return jsonify({
        "health_data": health_data,
        "weather_data": weather_data,
        "insight": insight,
        "state": state
    })

# ============================
# RENDER CONFIG
# ============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Running on port {port}...")
    app.run(host="0.0.0.0", port=port)
