import os
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = 'uploads/maps'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists locally
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is permitted."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- MongoDB Connection ---
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

# --- API Endpoints ---

# [POST] Upload Image to local folder and save metadata to MongoDB
@app.route('/uploadImage', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"}), 400
        
        file = request.files['file']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            
            # Create a document for MongoDB
            img_doc = {
                "original_name": file.filename, 
                "url": f"/uploads/maps/{filename}"            
            }
            img_id = images_collection.insert_one(img_doc).inserted_id
            
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
        images = list(images_collection.find())
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
        result = images_collection.delete_one({"_id": ObjectId(image_id)})
        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "Image record deleted from database"}), 200
        return jsonify({"status": "error", "message": "Image not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Route to serve the actual image files to the browser/frontend
@app.route('/uploads/maps/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Flask runs on http://127.0.0.1:5000
    app.run(debug=True, port=5000)