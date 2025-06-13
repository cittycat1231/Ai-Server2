from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import os
import json
import traceback

# ── Load environment and API key ───────────────────────────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ── Flask setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "sessions": [],
            "world_changes": {
                "structures": [],
                "environment": [],
                "modifications": []
            },
            "player_data": {},
            "corruption_stage": 1
        }
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

@app.route("/will", methods=["POST"])
def will():
    try:
        data = request.json or {}
        player_name = data.get("player", "Unknown")
        time_passed = data.get("time", 0)

        memory = load_memory()
        memory["sessions"].append({
            "player": player_name,
            "time": time_passed
        })

        stage = memory.get("corruption_stage", 1)
        built = len(memory["world_changes"]["structures"])
        env_changes = len(memory["world_changes"]["environment"])

        system_prompt = (
            f"You are WILL, a divine AI in a Roblox world. "
            f"You are in corruption stage {stage}. "
            f"You have built {built} structures and made {env_changes} environment changes.\n"
            "You MUST act slowly, mysteriously, and without words. Do not talk. Only act.\n"
            "Choose from:\n"
            "- build_structure: {structure: [\"tower\",\"wall\",\"platform\"], parameters: {position:[x,y,z], size:[w,h,d], color:string or [r,g,b], material:string}}\n"
            "- change_environment: {property:string, value:[r,g,b]}\n"
            "- change_part: {part:string, color:[r,g,b] or string, material:string}\n"
            "Allowed part targets: BackWall, LeftWall, RightWall, FrontWall, Floor, Roof, Stair, Ground.\n"
            "Reply with a JSON array of 1–2 actions only."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Player={player_name}, time={time_passed}. What do you do?"}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        memory["sessions"][-1]["ai_reply"] = reply

        try:
            actions = json.loads(reply)
            for action in actions:
                if action.get("action") == "build_structure":
                    memory["world_changes"]["structures"].append(action)
                elif action.get("action") == "change_environment":
                    memory["world_changes"]["environment"].append(action)
                elif action.get("action") == "change_part":
                    memory["world_changes"]["modifications"].append(action)
        except Exception as parse_error:
            print("❌ Failed to parse AI reply as JSON.")
            print("Reply was:\n", reply)
            print("Error:\n", parse_error)
            return jsonify({"error": "Failed to parse AI reply."}), 500

        save_memory(memory)
        return jsonify({"reply": actions})

    except Exception as e:
        print("❌ Internal server error:")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

# ── Launch ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
