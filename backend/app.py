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
# ======================# Flask App Configuration# ======================
app = Flask(__name__)
# Environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "Qwen/Qwen3-Coder-30B-A3B-Instruct"  # The model to use
# Initialize the Hugging Face InferenceClient once for efficiency
if HF_TOKEN:
    client = InferenceClient(model=MODEL, token=HF_TOKEN, headers={"Accept-Encoding": "identity"})
else:
    client = None
# ======================# Helper Functions# ======================
def clean_code(code: str) -> str:
    """Trim whitespace and remove empty lines."""
    if not code:
        return ""
    lines = code.splitlines()
    # Remove leading and trailing whitespace from each line
    cleaned_lines = [line.strip() for line in lines]
    # Filter out any completely empty lines
    cleaned_lines = [line for line in cleaned_lines if line]
    return "\n".join(cleaned_lines)
def run_code_and_track_emissions(code: str, test_params: dict, language: str) -> float:
    """
    Measures the CO2 emissions of executing a given code string using a subprocess.
    This function creates a temporary script, wraps the provided code, and
    executes it as a new process to measure emissions.
    Args:
        code (str): The code to execute and measure.
        test_params (dict): A dictionary containing test case parameters.
        language (str): The language of the code ('python' or 'c').
    Returns:
        float: The average CO2 emissions in kg over multiple runs.
    """
    if not code.strip():
        print("Provided code is empty, returning 0.0 emissions.")
        return 0.0
    temp_file = None
    exec_file = None
    emissions_list = []
    num_runs = 3
    function_name = test_params.get('function_name', 'your_function')
    data_size = test_params.get('data_size', 100000)
    try:
        # Create a temporary file to hold the code
        if language == 'python':
            suffix = '.py'
            executable = [sys.executable]
            wrapped_code = f"""
import sys
import traceback
import json
from codecarbon import EmissionsTracker
import random
import time
{code}
# Test runner
if __name__ == "__main__":
    emissions_data = {{}}
    try:
        tracker = EmissionsTracker()
        tracker.start()
        # A predictable, large test case
        large_list = list(range({data_size}))
        target = large_list[int({data_size} / 2)]
        try:
            func_to_call = locals().get('{function_name}')
            if callable(func_to_call):
                # Check for correct number of arguments to avoid type errors
                if '{function_name}' == 'find_first_occurrence':
                    func_to_call(target, large_list)
                else:
                    func_to_call() # Assuming no args for other functions
            else:
                for _ in range(10000000):
                    _ = 1 + 1
        except Exception as e:
            print(f"Error during user code execution: {{e}}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        emissions = tracker.stop()
        emissions_data['emissions'] = emissions
    except Exception as e:
        emissions_data['error'] = str(e)
        traceback.print_exc(file=sys.stderr)
    print(json.dumps(emissions_data))
"""
        elif language == 'c':
            suffix = '.c'
            wrapped_code = f"""
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
{code}
// Test runner function
int main() {{
    int* large_array = (int*)malloc({data_size} * sizeof(int));
    int target;
    if (large_array == NULL) {{
        fprintf(stderr, "Memory allocation failed.\\n");
        return 1;
    }}
    for (int i = 0; i < {data_size}; i++) {{
        large_array[i] = i;
    }}
    target = large_array[({data_size} / 2)];
    // We don't have a direct C codecarbon equivalent, so we just run the code
    // The Python tracker will measure the CPU time of this process
    {function_name}(large_array, {data_size}, target);
    free(large_array);
    return 0;
}}
"""
        else:
            raise ValueError("Unsupported language")
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            temp_file = f.name
            f.write(wrapped_code)
            f.flush()
        if language == 'c':
            # Compile the C code
            exec_file = temp_file.replace('.c', '')
            compile_result = subprocess.run(['gcc', temp_file, '-o', exec_file], capture_output=True, text=True, timeout=60)
            if compile_result.returncode != 0:
                print(f"Compilation failed:\n{compile_result.stderr}", file=sys.stderr)
                return 0.0 # Return 0 emissions on compilation failure
            executable = [exec_file]
        for i in range(num_runs):
            print(f"Starting measurement run {i+1} of {num_runs}...")
            # Start the tracker before the subprocess call
            tracker = EmissionsTracker()
            tracker.start()
            # The subprocess executes the code
            result = subprocess.run(
                executable,
                capture_output=True,
                text=True,
                timeout=120
            )
            # Stop the tracker after the subprocess finishes
            emissions = tracker.stop()
            emissions_list.append(emissions)
            if result.stderr:
                print(f"Subprocess returned errors:\n{result.stderr}", file=sys.stderr)
            # For Python, parse JSON output from the subprocess stdout
            if language == 'python':
                try:
                    output = json.loads(result.stdout)
                    if 'error' in output:
                        print(f"Error in subprocess execution: {output['error']}", file=sys.stderr)
                        break
                except json.JSONDecodeError:
                    print("Failed to decode JSON from subprocess output.")
                    print(f"Subprocess output was:\n{result.stdout}", file=sys.stderr)
                    break
            # Give a little break between runs
            time.sleep(1)
        if emissions_list:
            average_emissions = statistics.mean(emissions_list)
            print(f"Measurements: {emissions_list}")
            print(f"Average Emissions: {average_emissions}")
            return average_emissions
        else:
            return 0.0
    except subprocess.TimeoutExpired:
        print("Code execution timed out.")
        return 0.0
    except Exception as e:
        print(f"Error measuring emissions: {e}")
        return 0.0
    finally:
        # Clean up temporary files
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        if exec_file and os.path.exists(exec_file):
            os.remove(exec_file)
# ======================# Flask Endpoints# ======================
@app.route("/ping", methods=["GET"])
def ping():
    """A simple health check endpoint."""
    return jsonify({"status": "pong", "message": "Backend is running"}), 200
@app.route("/codegen", methods=["POST"])
def codegen():
    """Generates code and measures its CO2 footprint."""
    try:
        data = request.json or {}
        prompt = data.get("prompt", "")
        language = data.get("language", "python")
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        if client is None:
            return jsonify({"error": "Hugging Face API token not set."}), 500
        # Augment prompt for LLM based on language
        system_prompt = "You are a helpful coding assistant. Generate clear, concise, and efficient code based on the user's prompt."
        if language == 'c':
            system_prompt = "You are a helpful C programming assistant. Generate clear, concise, and efficient C code based on the user's prompt. Provide the code in a single block without any additional text."
            full_prompt = f"Generate a C function that {prompt}."
        else:
            full_prompt = prompt
        tracker = EmissionsTracker()
        tracker.start()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        result = client.chat_completion(messages=messages, max_tokens=800)
        llm_co2_kg = tracker.stop()
        code = clean_code(result.choices[0].message.content)
        # Now, run and measure the CO2 of the generated code
        execution_co2_kg = run_code_and_track_emissions(code, {"function_name": "dummy_function", "data_size": 1}, language)
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
        traceback_str = traceback.format_exc()
        print("Exception occurred:\n", traceback_str)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
@app.route("/optimize", methods=["POST"])
def optimize():
    """Optimizes a provided code snippet and measures its CO2 savings."""
    try:
        data = request.json or {}
        unoptimized_code = data.get("code", "")
        language = data.get("language", "python")
        if not unoptimized_code:
            return jsonify({"error": "No code provided for optimization"}), 400
        if client is None:
            return jsonify({"error": "Hugging Face API token not set."}), 500
        # Define a consistent test case for both versions
        test_case_params = {
            "function_name": "find_first_occurrence",
            "data_size": 1000000
        }
        # Measure CO2 for the original unoptimized code
        co2_before_kg = run_code_and_track_emissions(unoptimized_code, test_case_params, language)
        # Craft a prompt for the optimizer LLM
        optimization_prompt = f"""
The following {language} code is inefficient. Your task is to provide an optimized version that reduces its energy consumption.
Unoptimized code:
```{language}
{unoptimized_code}
Provide only the final optimized {language} code, no additional text or explanations.
"""
        tracker_optimize = EmissionsTracker()
        tracker_optimize.start()
        messages = [
            {"role": "system", "content": f"You are a skilled {language} code optimizer. Respond with the optimized code."},
            {"role": "user", "content": optimization_prompt}
        ]
        result = client.chat_completion(messages=messages, max_tokens=800)
        llm_co2_kg = tracker_optimize.stop()
        optimized_response = result.choices[0].message.content
        # Extract the code block from the LLM's response
        optimized_code = clean_code(optimized_response.split(f"```{language}")[-1].split("```")[0])
        # Measure CO2 for the newly optimized code
        co2_after_kg = run_code_and_track_emissions(optimized_code, test_case_params, language)
        return jsonify({
            "optimized_code": optimized_code,
            "before_co2": co2_before_kg,
            "after_co2": co2_after_kg,
            "llm_co2_kg": llm_co2_kg
        })
    except HfHubHTTPError as e:
        return jsonify({"error": f"Hugging Face Hub API error: {str(e)}"}), 500
    except Exception as e:
        traceback_str = traceback.format_exc()
        print("Exception occurred:\n", traceback_str)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
