# app.py
from flask import Flask, request, jsonify
# Import the main validation function from your finalized parser file
from src.parser import validate_query 
from flask_cors import CORS # Required for the frontend (index.html) to work

app = Flask(__name__)
CORS(app) # Enable CORS for cross-origin requests

# Basic endpoint for health check
@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "running", "message": "SQL Validator API is operational."})

# Main validation endpoint
@app.route('/api/validate', methods=['POST'])
def validate_sql():
    # 1. Get the SQL query from the incoming JSON request
    data = request.get_json()

    if not data or 'query' not in data:
        return jsonify({"valid": False, "error_message": "Missing 'query' field in request body."}), 400

    query = data['query']

    # 2. Run the validation
    result_string = validate_query(query)

    # 3. Parse the result string to create a proper JSON response
    if result_string.startswith("✅"):
        # The query is valid
        return jsonify({
            "valid": True,
            "message": result_string.replace("✅ VALIDATION SUCCESS: ", "")
        }), 200
    else:
        # The query is invalid. Parse the error message.
        error_parts = result_string.split(': ', 2)
        error_type = error_parts[1].split(':', 1)[0] if len(error_parts) > 1 else "Unknown Error"
        error_message = error_parts[-1]

        return jsonify({
            "valid": False,
            "error_type": error_type.strip(),
            "error_message": error_message.strip()
        }), 200 

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, port=5000)