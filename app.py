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
    """Generate simulated wellness data, or use POSTed JSON values."""
    if posted_data:
        # Use provided POST values (ReqBin), fallback to random if missing
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
        # GET request = full simulation
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
# AI INSIGHT GENERATION
# ============================
def get_ai_insight(health_data, weather_data):
    try:
        prompt = f"""
        You are a wellness coach. Based on these metrics and the weather,
        give ONE short, positive, actionable insight under 20 words.

        Health Data:
        {json.dumps(health_data, indent=2)}

        Weather:
        {json.dumps(weather_data, indent=2)}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Provide short friendly wellness advice."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 50
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]

        return "AI unavailable — maintaining good habits is enough today!"

    except Exception as e:
        return f"AI error: {str(e)} — stay hydrated!"

# ============================
# MAIN ROUTE (GET + POST)
# ============================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        posted_data = request.get_json()   # ReqBin POST body
    else:
        posted_data = None                 # GET → random data

    health_data = generate_health_data(posted_data)
    weather_data = get_weather()
    insight = get_ai_insight(health_data, weather_data)

    return jsonify({
        "health_data": health_data,
        "weather_data": weather_data,
        "insight": insight
    })

# ============================
# RENDER SERVER CONFIG
# ============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Running on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
