from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# ✅ Hugging Face token (set your own in env)
HF_TOKEN = os.getenv("HF_TOKEN", None)
MODEL = "bigcode/starcoder"  # or whichever model you use

@app.route("/codegen", methods=["POST"])
def codegen():
    try:
        data = request.json
        prompt = data.get("prompt", "")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # ⚡ If HF token not set, fallback with dummy code
        if not HF_TOKEN:
            code = f"# Dummy code for: {prompt}\nprint('Hello CodeLeaf! 🌱')"
            return jsonify({"code": code, "co2_kg": 0.000123})

        # ✅ Call Hugging Face Inference API
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 200}}
        MODEL = "microsoft/phi2"
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{MODEL}",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return jsonify({"error": f"HF API error: {response.text}"}), 500

        result = response.json()
        # Extract text depending on model output
        if isinstance(result, list) and "generated_text" in result[0]:
            code = result[0]["generated_text"]
        else:
            code = str(result)

        return jsonify({
            "code": code,
            "co2_kg": 0.000123  # replace with real calc later
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
