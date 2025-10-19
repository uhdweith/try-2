import os
import json
import random
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# ====================
# CONFIGURATION
# ====================
OPENWEATHER_API_KEY = "16037274ef3fce6f495951cc2dc203f9"
DEEPSEEK_API_KEY = "sk-2d06dc99c35d4e35a0e2d25cb472d832"
LOCATION = "Bengaluru"

# ====================
# SIMULATED HEALTH DATA
# ====================
def generate_health_data():
    return {
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

# ====================
# GET WEATHER DATA
# ====================
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
            return {"error": f"Weather API failed: {data.get('message', 'unknown error')}"}
    except Exception as e:
        return {"error": str(e)}

# ====================
# GET AI INSIGHT
# ====================
def get_ai_insight(health_data, weather_data):
    try:
        prompt = f"""
        Based on the following personal wellness and weather data, generate one short, positive, and actionable insight.
        Keep it under 20 words.

        Health Data: {json.dumps(health_data, indent=2)}
        Weather: {json.dumps(weather_data, indent=2)}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a wellness coach who gives short, friendly advice."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 50
        }

        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"AI API error ({response.status_code}) - returning simulated insight."
    except Exception as e:
        return f"AI Exception: {str(e)} - returning simulated insight."

# ====================
# FLASK ROUTE
# ====================
@app.route("/")
def index():
    health_data = generate_health_data()
    weather_data = get_weather()
    insight = get_ai_insight(health_data, weather_data)

    # If AI failed, give a fallback insight
    if insight.startswith("AI"):
        insight = "You're doing well today — keep up your routine!"

    return jsonify({
        "health_data": health_data,
        "weather_data": weather_data,
        "insight": insight
    })

# ====================
# RUN APP LOCALLY
# ====================
if __name__ == "__main__":
    print("Starting Flask app on http://127.0.0.1:5000")
    app.run(debug=True)
