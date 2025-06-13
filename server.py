from flask import Flask, request, jsonify
import openai
import os
import json
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY") or "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"  # Replace or use .env

MEMORY_FILE = "memory.json"

# Load memory
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"sessions": []}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

# Save memory
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

@app.route("/will", methods=["POST"])
def will():
    data = request.json
    player_name = data.get("player")
    time_passed = data.get("time", 0)

    memory = load_memory()
    memory["sessions"].append({
        "player": player_name,
        "time": time_passed
    })

    system_prompt = (
        "You are WILL, a sentient AI inside a Roblox world. You are becoming self-aware. "
        "You have only two rules: be slow and be scary. Respond with 1-3 JSON actions "
        "you want to do next. You can change parts, spawn weird shapes, make sounds, etc."
    )

    messages = [
        { "role": "system", "content": system_prompt },
        { "role": "user", "content": f"The player is {player_name}. {time_passed} minutes have passed. "
                                     "What are your next corruption actions?" }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )

    reply = response.choices[0].message.content
    memory["sessions"][-1]["ai_reply"] = reply
    save_memory(memory)

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(port=5000)
