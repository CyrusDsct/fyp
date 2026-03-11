#flask backend
import os
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openrouter import OpenRouter
from datetime import datetime
import base64


# Load variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = 'uploads/maps'
DATA_FOLDER = 'uploads/data' 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATA_FOLDER'] = DATA_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is permitted."""
    # This logic now automatically includes .csv because of the set above
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- MongoDB Connection 
# We retrieve the URI from the environment variable for security
MONGO_URI = os.getenv("MONGO_URI")

# tlsAllowInvalidCertificates=True solves local SSL handshake issues

client = MongoClient(
    MONGO_URI,
    tlsAllowInvalidCertificates=True 
)

db = client["MapAuditDB"]
results_collection = db["analysis_results"]
images_collection = db["map_images"]
# Define the collection for CSV data
data_collection = db["map_data"]

# --- API Endpoints ---

# [POST] Updated to handle separate folders
@app.route('/uploadImage', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400
        
        file = request.files['file']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # 1. Logic to separate folders
            if filename.lower().endswith('.csv'):
                save_dir = app.config['DATA_FOLDER']
                url_path = f"/uploads/data/{filename}"
                target_collection = data_collection
            else:
                save_dir = app.config['UPLOAD_FOLDER']
                url_path = f"/uploads/maps/{filename}"
                target_collection = images_collection
            
            save_path = os.path.join(save_dir, filename)
            file.save(save_path)
            
            # Create a document for MongoDB
            img_doc = {
                "original_name": file.filename, 
                "url": url_path            
            }
            # Insert into the specific collection determined by the file type
            img_id = target_collection.insert_one(img_doc).inserted_id
            
            return jsonify({
                "status": "success", 
                "image_id": str(img_id), 
                "url": img_doc["url"]
            }), 200
            
        return jsonify({"status": "error", "message": "Invalid file type"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# [GET] Retrieve all uploaded maps from MongoDB
@app.route('/readImage', methods=['GET'])
def read_images():
    try:
        # Combine data from both collections for the gallery
        images = list(images_collection.find()) + list(data_collection.find())
        # Convert ObjectId to string for JSON serialization
        for img in images:
            img['_id'] = str(img['_id'])
        return jsonify({"status": "success", "data": images}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# [DELETE] Delete a specific map by ID
@app.route('/deleteImage/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    try:
        # Search both collections for the ID
        img_data = images_collection.find_one({"_id": ObjectId(image_id)}) or data_collection.find_one({"_id": ObjectId(image_id)})
        
        if not img_data:
            return jsonify({"status": "error", "message": "Image not found in database"}), 404

        file_path = img_data['url'].lstrip('/') 

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Physical file deleted: {file_path}")

        # Remove from whichever collection it exists in
        result = images_collection.delete_one({"_id": ObjectId(image_id)})
        if result.deleted_count == 0:
            result = data_collection.delete_one({"_id": ObjectId(image_id)})
        
        if result.deleted_count > 0:
            return jsonify({
                "status": "success", 
                "message": "database record deleted successfully"
            }), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

#Add route to serve files from the folder
@app.route('/uploads/data/<filename>')
def serve_data(filename):
    return send_from_directory(app.config['DATA_FOLDER'], filename)

@app.route('/uploads/maps/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# LLM Analysis 
@app.route('/analyzeMap/<image_id>', methods=['POST'])
def analyze_map(image_id):
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify({"error": "Missing OPENROUTER_API_KEY"}), 500

        print("🔥 ANALYZE MAP HIT:", image_id)
        print("API KEY PRESENT:", bool(api_key))

        img = images_collection.find_one({"_id": ObjectId(image_id)})
        if not img:
            return jsonify({"error": "Image not found"}), 404

        image_path = img['url'].lstrip('/')
        print("image_path:", image_path, "exists?", os.path.exists(image_path))

        if not os.path.exists(image_path):
            return jsonify({"error": "Image file missing"}), 404

        # Encode image
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        prompt = open("prompt.txt")

        with OpenRouter(api_key=api_key) as client:
            response = client.chat.send(
                model="openai/gpt-5o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            )


        try:
            analysis_output = response.choices[0].message.content
        except Exception as parse_err:
            print("ERROR parsing response:", repr(parse_err))
            print("RAW RESPONSE:", response)
            return jsonify({
                "error": "Failed to parse OpenRouter response",
                "raw_response": str(response)
            }), 500

        results_collection.insert_one({
            "image_id": image_id,
            "analysis": analysis_output,
            "created_at": datetime.utcnow()
        })

        return jsonify({
            "status": "success",
            "analysis": analysis_output
        }), 200

    except Exception as e:
        print("ERROR in /analyzeMap:", repr(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
