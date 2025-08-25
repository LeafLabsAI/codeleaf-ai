from flask import Flask, request, jsonify
from huggingface_hub import InferenceClient
from codecarbon import EmissionsTracker
from dotenv import load_dotenv
import os

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")  # add this later to .env (not committed)

app = Flask(__name__)
client = InferenceClient("bigcode/starcoder", token=HF_TOKEN)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"msg": "CodeLeaf AI Backend 🌱"})

@app.route("/codegen", methods=["POST"])
def codegen():
    body = request.get_json(force=True)
    prompt = body.get("prompt", "")

    tracker = EmissionsTracker(measure_power_secs=1, log_level="warning")
    tracker.start()
    result = client.text_generation(
        f"Write clean, efficient Python code. {prompt}\n",
        max_new_tokens=180
    )
    emissions = tracker.stop()  # kg CO2eq (estimate)
    return jsonify({"code": result, "co2_kg": emissions})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
