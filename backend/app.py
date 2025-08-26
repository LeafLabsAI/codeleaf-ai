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

# ======================
# Flask App Configuration
# ======================
app = Flask(__name__)

# Environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL = "Qwen/Qwen3-Coder-30B-A3B-Instruct"  # The model to use

# Initialize the Hugging Face InferenceClient once for efficiency
if HF_TOKEN:
    client = InferenceClient(model=MODEL, token=HF_TOKEN)
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

def run_code_and_track_emissions(code: str) -> float:
    """
    Measures the CO2 emissions of executing a given code string by running it
    multiple times and returning the average. This approach mitigates the
    effect of system noise and provides a more stable reading.
    
    Args:
        code (str): The Python code to execute and measure.
        
    Returns:
        float: The average CO2 emissions in kg over multiple runs.
    """
    if not code.strip():
        print("Provided code is empty, returning 0.0 emissions.")
        return 0.0

    temp_file = None
    emissions_list = []
    
    # We will run the code multiple times and average the results
    # Reduced from 5 to 3 runs for faster performance.
    num_runs = 3
    
    try:
        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name
            
            # Wrap the user's code in a large loop to increase execution time
            wrapped_code = f"""
import sys
import time
import traceback

def main():
    try:
        # Your provided code goes here
        {code}
        # End of provided code
    except Exception as e:
        print(f"Error during code execution: {{e}}", file=sys.stderr)
        traceback.print_exc()
    
if __name__ == "__main__":
    # Run the user's code 10,000,000 times within each measurement
    # This ensures a high signal-to-noise ratio
    for _ in range(10000000):
        main()
"""
            f.write(wrapped_code)
            f.flush()

        # Run the subprocess multiple times and collect the emissions
        for i in range(num_runs):
            print(f"Starting measurement run {i+1} of {num_runs}...")
            # Initialize the EmissionsTracker
            tracker = EmissionsTracker()
            
            # Start the tracker
            tracker.start()
            
            # Execute the temporary file. `subprocess.run` is more robust.
            result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True, timeout=60)
            
            # Stop the tracker and get the emissions value
            emissions = tracker.stop()
            emissions_list.append(emissions)
            
            if result.stderr:
                print(f"Subprocess returned errors:\n{result.stderr}")
        
        # Calculate the average emissions from all runs
        if emissions_list:
            average_emissions = statistics.mean(emissions_list)
            print(f"Measurements: {emissions_list}")
            print(f"Average Emissions: {average_emissions}")
            return average_emissions
        else:
            return 0.0
            
    except subprocess.TimeoutExpired:
        print("Code execution timed out after 60 seconds.")
        return 0.0
    except Exception as e:
        print(f"Error measuring emissions: {e}")
        return 0.0
    finally:
        # Clean up the temporary file
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
            max_tokens=200
        )
        
        # Stop the tracker and get the emissions value
        llm_co2_kg = tracker.stop()

        code = clean_code(result.choices[0].message.content)
        
        # Now, run and measure the CO2 of the generated code
        execution_co2_kg = run_code_and_track_emissions(code)
        
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

        # Measure CO2 for the original unoptimized code
        co2_before_kg = run_code_and_track_emissions(unoptimized_code)
        
        # Craft a prompt for the optimizer LLM
        optimization_prompt = f"""
        The following Python code is inefficient. Your task is to provide an optimized version that reduces its energy consumption. Explain the changes briefly, and then provide only the final optimized code.

        Unoptimized code:
        {unoptimized_code}

        Optimized code:
        """

        # Use the tracker to measure emissions of the AI call for optimization
        tracker_optimize = EmissionsTracker()
        tracker_optimize.start()

        messages = [
            {"role": "system", "content": "You are a highly skilled Python code optimizer. Your goal is to improve code efficiency and reduce its environmental impact. Respond with the optimized code and a brief explanation of the changes."},
            {"role": "user", "content": optimization_prompt}
        ]

        result = client.chat_completion(
            messages=messages,
            max_tokens=300
        )
        
        # Stop the tracker and get the emissions value
        llm_co2_kg = tracker_optimize.stop()

        optimized_response = result.choices[0].message.content
        
        # Extract the code block from the LLM's response
        optimized_code = clean_code(optimized_response.split("```python")[-1].split("```")[0])

        # Measure CO2 for the newly optimized code
        co2_after_kg = run_code_and_track_emissions(optimized_code)

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
