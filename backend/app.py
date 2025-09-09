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

# ======================
# Flask App Configuration
# ======================
app = Flask(__name__)

# Environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "Qwen/Qwen3-Coder-30B-A3B-Instruct"  # The model to use

# Initialize the Hugging Face InferenceClient once for efficiency
if HF_TOKEN:
    client = InferenceClient(model=MODEL, token=HF_TOKEN, headers={"Accept-Encoding": "identity"})
else:
    client = None

# ======================
# Helper Functions
# ======================
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

def run_code_and_track_emissions(code: str, test_params: dict) -> float:
    """
    Measures the CO2 emissions of executing a given code string using a subprocess.
    This function creates a temporary Python script that wraps the provided code
    in a `codecarbon` tracker and a test runner. It then executes this script
    as a new process and parses the emissions output from its stdout.

    Args:
        code (str): The Python code to execute and measure.
        test_params (dict): A dictionary containing test case parameters.
            - 'function_name': The name of the function to be tested.
            - 'data_size': An integer for the size of the test data.

    Returns:
        float: The average CO2 emissions in kg over multiple runs.
    """
    if not code.strip():
        print("Provided code is empty, returning 0.0 emissions.")
        return 0.0

    temp_file = None
    emissions_list = []
    num_runs = 3
    
    function_name = test_params.get('function_name', 'your_function')
    data_size = test_params.get('data_size', 100000)
    
    # We need a predictable, large test case to highlight performance differences
    test_case_setup = f"""
import random
large_list = list(range({data_size}))
target = large_list[int({data_size} / 2)]
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name
            
            # The test script includes the provided code, the test runner,
            # and the codecarbon tracker
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
        # Initialize and start the tracker within this subprocess
        tracker = EmissionsTracker()
        tracker.start()

        {test_case_setup}
        
        # Call the user's function with the large test data
        try:
            # We use a try-except block here to handle cases where the function might not exist
            # or the parameters are incorrect.
            # This is a safe way to execute the user's code.
            func_to_call = locals().get('{function_name}')
            if callable(func_to_call):
                func_to_call(target, large_list)
            else:
                # If the function is not found, run a default heavy operation
                print("Function not found, running default CPU-intensive loop...", file=sys.stderr)
                for _ in range(10000000):
                    _ = 1 + 1
        except Exception as e:
            # We catch the exception and print it for debugging, but don't fail the emissions
            # measurement. This allows us to still get a baseline reading.
            print(f"Error during user code execution: {{e}}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

        # Stop the tracker and get the emissions
        emissions = tracker.stop()
        emissions_data['emissions'] = emissions

    except Exception as e:
        emissions_data['error'] = str(e)
        traceback.print_exc(file=sys.stderr)
    
    # Print the result as a JSON object for the parent process to parse
    print(json.dumps(emissions_data))
"""
            f.write(wrapped_code)
            f.flush()

        for i in range(num_runs):
            print(f"Starting measurement run {i+1} of {num_runs}...")
            
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=120  # Increased timeout for large data sizes
            )

            # Check for subprocess errors
            if result.stderr:
                print(f"Subprocess returned errors:\n{result.stderr}")
            
            # Attempt to parse the JSON output
            try:
                output = json.loads(result.stdout)
                if 'emissions' in output:
                    emissions_list.append(output['emissions'])
                elif 'error' in output:
                    print(f"Error in subprocess execution: {output['error']}")
                    break # Stop if there's an error
            except json.JSONDecodeError:
                print("Failed to decode JSON from subprocess output.")
                print(f"Subprocess output was:\n{result.stdout}")
                break

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
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

# ======================
# Flask Endpoints
# ======================
@app.route("/codegen", methods=["POST"])
def codegen():
    """Generates code and measures its CO2 footprint."""
    try:
        data = request.json or {}
        prompt = data.get("prompt", "")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        if client is None:
            return jsonify({
                "error": "Hugging Face API token not set. Please set the HF_TOKEN environment variable."
            }), 500

        # Use the tracker to measure emissions of the AI call
        tracker = EmissionsTracker()
        tracker.start()
        
        messages = [
            {"role": "system", "content": "You are a helpful coding assistant. Generate clear, concise, and efficient Python code based on the user's prompt."},
            {"role": "user", "content": prompt}
        ]
        
        result = client.chat_completion(
            messages=messages,
            max_tokens=800
        )
        
        # Stop the tracker and get the emissions value
        llm_co2_kg = tracker.stop()

        code = clean_code(result.choices[0].message.content)
        
        # Now, run and measure the CO2 of the generated code
        # We use a dummy test case here as we don't know the function or its purpose.
        execution_co2_kg = run_code_and_track_emissions(code, {"function_name": "dummy_function", "data_size": 1})
        
        if not code:
            code = "# No code generated."

        # Return a single key 'total_co2_kg' for the frontend to consume easily,
        # along with the detailed breakdown.
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

        if not unoptimized_code:
            return jsonify({"error": "No code provided for optimization"}), 400

        if client is None:
            return jsonify({"error": "Hugging Face API token not set. Please set the HF_TOKEN environment variable."}), 500

        # Define a consistent test case for both versions
        test_case_params = {
            "function_name": "find_first_occurrence",
            "data_size": 1000000
        }

        # Measure CO2 for the original unoptimized code
        co2_before_kg = run_code_and_track_emissions(unoptimized_code, test_case_params)
        
        # Craft a prompt for the optimizer LLM
        optimization_prompt = f"""
The following Python code is inefficient. Your task is to provide an optimized version that reduces its energy consumption.

Unoptimized code:
```python
{unoptimized_code}
```

Provide only the final optimized Python code, no additional text or explanations.
"""

        # Use the tracker to measure emissions of the AI call for optimization
        tracker_optimize = EmissionsTracker()
        tracker_optimize.start()

        messages = [
            {"role": "system", "content": "You are a highly skilled Python code optimizer. Your goal is to improve code efficiency and reduce its environmental impact. Respond with the optimized code."},
            {"role": "user", "content": optimization_prompt}
        ]

        result = client.chat_completion(
            messages=messages,
            max_tokens=800
        )
        
        # Stop the tracker and get the emissions value
        llm_co2_kg = tracker_optimize.stop()

        optimized_response = result.choices[0].message.content
        
        # Extract the code block from the LLM's response
        optimized_code = clean_code(optimized_response.split("```python")[-1].split("```")[0])

        # Measure CO2 for the newly optimized code
        co2_after_kg = run_code_and_track_emissions(optimized_code, test_case_params)

        return jsonify({
            "optimized_code": optimized_code,
            "before_co2": co2_before_kg,
            "after_co2": co2_after_kg,
            "llm_co2_kg": llm_co2_kg # This is the CO2 for the LLM call itself
        })

    except HfHubHTTPError as e:
        return jsonify({"error": f"Hugging Face Hub API error: {str(e)}"}), 500
    except Exception as e:
        traceback_str = traceback.format_exc()
        print("Exception occurred:\n", traceback_str)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
