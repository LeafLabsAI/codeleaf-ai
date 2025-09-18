from flask import Flask, request, jsonify
import os
import traceback
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from codecarbon import EmissionsTracker
import tempfile
import sys
import subprocess
import time
import statistics
import json
import psutil
import platform
import re
import logging

# Set codecarbon to info level for detailed logs
logging.getLogger("codecarbon").setLevel(logging.INFO)

# ====================== Flask App Configuration ======================
app = Flask(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "Qwen/Qwen3-Coder-30B-A3B-Instruct"

if HF_TOKEN:
    client = InferenceClient(model=MODEL, token=HF_TOKEN, headers={"Accept-Encoding": "identity"})
else:
    client = None

# ====================== Helper Functions ======================
def clean_code(code: str) -> str:
    """Remove markdown code fences and unwanted annotations."""
    if not code:
        return ""
    # Remove common markdown fences
    for fence in ["```python", "```c", "```"]:
        code = code.replace(fence, "")
    # Remove bold markdown
    code = re.sub(r"\*\*.*?\*\*", "", code)
    # Remove numbered optimization lists
    code = re.sub(r"^\s*\d+\..*$", "", code, flags=re.MULTILINE)
    # Remove lines containing Energy, Complexity, or Optimizations
    code_lines = [
        line for line in code.splitlines()
        if line.strip() and not re.match(r'^\s*Energy|Complexity|Optimizations', line)
    ]
    return "\n".join(code_lines)


def universal_emissions_tracker(executable, num_runs=3) -> float:
    """
    Rough CO2 estimate for non-Python code (C) using CPU time and system power assumptions.
    """
    emissions_list = []
    try:
        for _ in range(num_runs):
            start_time = time.time()
            # Provide empty input to prevent hangs on interactive prompts like scanf
            subprocess.run(executable, input="", capture_output=True, text=True, timeout=300)
            elapsed = time.time() - start_time

            cpu_count = psutil.cpu_count(logical=True)
            cpu_power_w = 45 if platform.system() != "Windows" else 65
            gpu_power_w = 300

            energy_kwh = ((cpu_power_w * cpu_count) + gpu_power_w) * elapsed / 3600
            co2_kg = energy_kwh * 0.475
            emissions_list.append(co2_kg)
    except Exception as e:
        print(f"Error in universal tracker: {e}")
        return 0.0
    return statistics.mean(emissions_list) if emissions_list else 0.0


def run_code_and_track_emissions(code: str, test_params: dict, language: str) -> float:
    """
    Executes code safely and tracks CO2 emissions.
    Python uses CodeCarbon, C uses universal tracker.
    """
    if not code.strip():
        return 0.0

    temp_file = None
    exec_file = None

    try:
        if language.lower() == "python":
            function_name = test_params.get("function_name", "dummy_function")
            data_size = test_params.get("data_size", 1000)
            wrapped_code = f"""
import sys, traceback, json
from codecarbon import EmissionsTracker
import logging

# Also set logger level inside the subprocess
logging.getLogger("codecarbon").setLevel(logging.INFO)

{code}

tracker = EmissionsTracker(save_to_file=False)
tracker.start()
try:
    func = locals().get('{function_name}')
    if callable(func):
        try:
            func(list(range({data_size})), {data_size}, {data_size}//2)
        except TypeError:
            func()
except Exception as e:
    print("ERROR:", e, file=sys.stderr)
emissions = tracker.stop()
"""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                temp_file = f.name
                f.write(wrapped_code)
                f.flush()

            executable = [sys.executable, temp_file]
            
            tracker = EmissionsTracker(save_to_file=False)
            tracker.start()
            # Provide empty input to prevent hangs on interactive prompts like input()
            subprocess.run(executable, input="", capture_output=True, text=True, timeout=300)
            emissions = tracker.stop()
            return emissions if emissions is not None else 0.0

        elif language.lower() == "c":
            code = clean_code(code)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
                temp_file = f.name
                f.write(code) # Use the cleaned code directly without wrapping
                f.flush()

            exec_file = temp_file.replace(".c", "")
            compile_res = subprocess.run(["gcc", temp_file, "-o", exec_file],
                                         capture_output=True, text=True, timeout=120)
            if compile_res.returncode != 0:
                print("C compilation failed:", compile_res.stderr)
                return 0.0
            return universal_emissions_tracker([exec_file])

        else:
            return 0.0

    except Exception as e:
        print(f"Error: {e}\n{traceback.format_exc()}")
        return 0.0
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        if exec_file and os.path.exists(exec_file):
            os.remove(exec_file)

# ====================== Flask Endpoints ======================
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "pong", "message": "Backend is running"}), 200


@app.route("/codegen", methods=["POST"])
def codegen():
    try:
        data = request.json or {}
        prompt = data.get("prompt", "")
        language = data.get("language", "python")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        if client is None:
            return jsonify({"error": "Hugging Face API token not set."}), 500

        system_prompt = f"You are a helpful {language} coding assistant. Generate clear, concise, carbon and power efficient short code. Provide only the code block with best case time and space complexity with proper executable format. Do not include any comments or explanations.Generate full code with necessary imports and definitions like main() dont just generate function definitions only."
        full_prompt = f"Generate a {language} function that {prompt}."

        start_time = time.time()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        result = client.chat_completion(messages=messages)
        request_time = time.time() - start_time

        code = clean_code(result.choices[0].message.content)

        # Estimate LLM CO2
        cpu_count = psutil.cpu_count(logical=True)
        cpu_power_w = 45 * 0.03
        gpu_power_w = 300 * 0.03
        energy_kwh = ((cpu_power_w * cpu_count) + gpu_power_w) * request_time / 3600
        llm_co2_kg = energy_kwh * 0.475

        execution_co2_kg = run_code_and_track_emissions(code, {}, language)

        if not code:
            code = f"# No {language} code generated."

        return jsonify({
            "code": code,
            "llm_co2_kg": llm_co2_kg,
            "execution_co2_kg": execution_co2_kg,
            "total_co2_kg": llm_co2_kg + execution_co2_kg
        })

    except HfHubHTTPError as e:
        return jsonify({"error": f"Hugging Face Hub API error: {str(e)}"}), 500
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/optimize", methods=["POST"])
def optimize():
    try:
        data = request.json or {}
        unoptimized_code = data.get("code", "")
        language = data.get("language", "python")

        if not unoptimized_code:
            return jsonify({"error": "No code provided for optimization"}), 400
        if client is None:
            return jsonify({"error": "Hugging Face API token not set."}), 500

        test_case_params = {"function_name": "find_first_occurrence", "data_size": 1000000}
        co2_before_kg = run_code_and_track_emissions(unoptimized_code, test_case_params, language)

        optimization_prompt = f"""
The following {language} code is inefficient. Provide an optimized version that reduces energy consumption and CO2 footprint with best-case space and time complexity but without any comments and in proper executable format without any extra text and explanations."
Unoptimized code:
{language} {unoptimized_code}
Provide only the optimized {language} code.
"""

        start_time = time.time()
        messages = [
            {"role": "system", "content": f"You are a skilled {language} code optimizer. Respond with the optimized code."},
            {"role": "user", "content": optimization_prompt}
        ]
        result = client.chat_completion(messages=messages)
        request_time = time.time() - start_time

        code_raw = clean_code(result.choices[0].message.content)

        # Estimate LLM CO2
        cpu_count = psutil.cpu_count(logical=True)
        cpu_power_w = 45 * 0.03
        gpu_power_w = 300 * 0.03
        energy_kwh = ((cpu_power_w * cpu_count) + gpu_power_w) * request_time / 3600
        llm_co2_kg = energy_kwh * 0.475

        co2_after_kg = run_code_and_track_emissions(code_raw, test_case_params, language)

        return jsonify({
            "optimized_code": code_raw,
            "before_co2": co2_before_kg,
            "after_co2": co2_after_kg,
            "llm_co2_kg": llm_co2_kg
        })

    except HfHubHTTPError as e:
        return jsonify({"error": f"Hugging Face Hub API error: {str(e)}"}), 500
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)