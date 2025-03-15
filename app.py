import os
import time
import json
from groq import Groq
import paho.mqtt.client as mqtt
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Placd KEYs in environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
COLLECTU_ADDRESS = os.getenv("COLLECTU_ADDRESS")
COLLECTU_API = os.getenv("COLLECTU_API")
COLLECTU_PASSWORD = os.getenv("COLLECTU_PASSWORD")

if not GROQ_API_KEY and not COLLECTU_ADDRESS and not COLLECTU_API:
    raise Exception("Missing environment variables")

groq_client = Groq(api_key=GROQ_API_KEY)

# --- MQTT ---
MQTT_BROKER = COLLECTU_ADDRESS
MQTT_PORT = 8883
MQTT_TOPIC = "Arena2036/ArenaX/PilzRobotics/RCCESOI1001_ED/Control"

API_TOKEN = COLLECTU_API

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.connected_flag = True
    else:
        print(f"Connection failed with code {rc}")

mqtt.Client.connected_flag = False
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(API_TOKEN, COLLECTU_PASSWORD)
mqtt_client.tls_set()
mqtt_client.tls_insecure_set(True)
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

while not mqtt_client.connected_flag:
    print("Waiting for connection...")
    time.sleep(1)


def map_task_to_predefined_action(user_task: str) -> str:
    """
    prompt mapping with user input
    """
    prompt = (
        "You have a set of 5 predefined robot action commands (AROUND_INSPECT, DANCE, CLOSE_INSPECT "
        "AROUND_INSPECT moves robot to 8 points for vague inspection, DANCE moves robo randomly "
        "CLOSE_INSPECT moves robot 4 points for precise quality "
        "Each command corresponds to a specific, hard-coded action on the robot as mentioned. "
        "Given the following task description, map it to the corresponding predefined action command(s). "
        "If multiple actions are needed, list them in a random order separated by commas. "
        "For random command give error as output, do not allow random inputs. "
        "Only return the command names without any additional explanation.\n\n"
        f"Task description: {user_task}"
    )

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile", # change model as needed
        )
        action_command = chat_completion.choices[0].message.content.strip()
        return action_command
    except Exception as e:
        return f"Error generating action command: {e}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_task = request.form.get("user_task")
        if not user_task:
            return jsonify({"status": "error", "message": "No task provided."}), 400
        action_command = map_task_to_predefined_action(user_task)
        if action_command.startswith("Error"):
            return jsonify({"status": "error", "message": action_command}), 500
        mqtt_message = json.dumps({"action": action_command})
        mqtt_client.publish(MQTT_TOPIC, mqtt_message)
        return jsonify({"status": "success", "command": action_command})
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
