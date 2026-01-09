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

# --- LLM Analysis  ---
@app.route('/analyzeMap/<image_id>', methods=['POST'])
def analyze_map(image_id):
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify({"error": "Missing OPENROUTER_API_KEY"}), 500

        img = images_collection.find_one({"_id": ObjectId(image_id)})
        if not img:
            return jsonify({"error": "Image not found"}), 404

        image_path = img['url'].lstrip('/')
        if not os.path.exists(image_path):
            return jsonify({"error": "Image file missing"}), 404

        # Encode image
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        # prompt for map input
        prompt = """
        TASK

        Given a choropleth map as the image input, extract information from the image and evaluate its quality according to the following instructions and guidelines. 

        Output the JSON text only. 

        Instructions 

        Read the guidelines to find out what information needs to be extracted from the map. 

        Read the map to extract the required information. 

        Fill in the blanks with the information extracted according to the output format provided to produce a JSON-formatted text for each data item. Meanwhile, keep track of the good/bad qualities found in each data item. 

        Append text to your response to factually and briefly explain the contents of the map, such as what it is about and any notable findings. 

        Use the information extracted, as well as the count of good/bad data items, to judge whether the map counts as good or bad. 

        Append text to your response to explain your reasoning for judging whether the map is good or bad. [“reasoning] 

        Check if the resulting JSON file is formatted correctly, and send it as your response. Output no other content. 

        Guidelines 

        Each data item required will be formatted as follows, with optional items enclosed in parentheses () and placeholders for text enclosed in angle brackets <>: 

        description:  

        (example: ) 

        (options: <the list of values to choose from, separated by /, or the type of values to respond with, enclosed in angle brackets>) 

        (good: ) 

        (bad: ) 

        ( description: (example: ) (options: <the list of values to choose from, separated by /, or the type of values to respond with, enclosed in angle brackets>) (good: ) (bad: )) 

        === 

        The following is the list of data items that need to be extracted from the input image of a choropleth map: 

        MAP TITLE 

        description: The title of the map 

        example: Population Density of the World 

        === 

        URL 

        description: A working link to the image source, if one is provided. Provide the URL only. 

        example: https://senseable.mit.edu/urban-exposures/ 

        options: [url]/None/Not Applicable 

        good: The link provided is accessible 

        bad: There is no link, or the link is broken 

        === 

        CITATIONS 

        description: The names or working links to the data sources used to make the map, if provided in the image. 

        examples: United Nations Yearly Report 2007–2008, data.worldbank.org 

        === 

        LEGEND 

        description: A key or guide on the map that explains how colors (or patterns) correspond to data values or categories, making it possible to interpret the map. 

        options: yes(present)/no(absent) 

        good: The bins should be clear and non-overlapping. The colors used should be distinguishable and match all the colors used in the map. The legend should not cover the contents of the map. 

        bad: No legend, unclear legend, colors in the legend do not correspond to the colors on the map, or the legend covers map features. 

        === 

        LEGEND ORIENTATION 

        description: Whether the values of the legend are listed horizontally or vertically. 

        options: horizontal/vertical/other/not applicable 

        === 

        RANGE 

        description: The range of data encompassed in the legend. For categorical or discretely divided data, each division should be listed as a separate item in a list. Convert all ranges into the form of [, ]. 

        example: [0,100]/[[0,10],[10,20],[20,30],[30,40],[40,50]]/[Healthy, Ill, Dead, Other, Not Applicable] 

        good: The bins are continuous, non-overlapping, and span the whole range of data shown in the map. 

        bad: There are gaps or overlaps in the bins, or missing data not accounted for in the legend. 

        === 

        NO DATA 

        description: Does the legend identify regions with no data? 

        options: yes/no/not applicable 

        good: A distinct color or symbol is used to indicate areas with no data. 

        bad: Regions with no data use the same color as low values, or there is no explicit indicator for regions with no data in the legend. 

        === 

        EXPLICIT “OTHER” CATEGORY 

        description: Indicates whether the legend includes an explicit “Other” category to account for data that does not fit into the main categories. 

        options: yes/no/not applicable 

        good: “Other” category included when needed. 

        bad: Missing “Other” category when needed, leaving data unaccounted for or ambiguous. 

        === 

        INCOMPLETE INFO 

        description: The map contains regions with colors that are not represented in the legend (except background color). 

        options: yes/no 

        good: no (all the data shown is represented in the legend) 

        bad: yes (the legend is missing some data shown) 

        === 

        DATA TYPE 

        description: The type of data represented in the legend. Definitions are as follows: Nominal: non-numerical categories with no inherent hierarchy (e.g., types of land use) Ordinal: non-numerical categories with a meaningful order (e.g., primary, secondary, tertiary) Ratio: numeric data with a true zero point Interval: numeric data with meaningful differences but no true zero 

        options: nominal/ordinal/interval/ratio 

        === 

        CONTIGUITY 

        description: Whether the data is represented as a continuous range or divided into discrete categories (bins) 

        options: yes/no/not applicable 

        === 

        NUMBER OF BINS 

        description: The number of divisions used to represent all data in the legend, including categories for No Data and Others if they exist. For continuous data, this property is not applicable. 

        options: 1/2/3/.../Not Applicable 

        good: 3–7 bins 

        bad: Too many = cluttered; Too few = oversimplified 

        === 

        COLOUR SCHEME 

        description: The range of colors used to represent data in the legend, excluding background and “No Data” colors. Definitions: Sequential Single-hue: single hue varying in lightness Sequential Multi-hue: multiple hues in ordered progression Categorical: distinct colors of similar brightness Diverging: two contrasting hues with midpoint Cyclic: continuous loop of hues (e.g., rainbow) Other: any unclassified scheme Not Applicable: when no color scheme can be defined 

        options: Sequential Single-hue/Sequential Multi-hue/Categorical/Diverging/Cyclic/Other/Not Applicable 

        good: Color scheme matches the data type 

        bad: Color scheme is inappropriate for the data type 

        == 

        COLOURS 

        description: A list of notable colors used in the legend, ordered left-to-right (horizontal) or top-to-bottom (vertical). Use simple color names only. 

        example: <white, blue>/<white, red, brown>/<yellow, red>/<red, yellow, green, blue> 

        good: Colors have logical association with the map’s meaning 

        bad: Arbitrary or confusing colors, indistinguishable hues, or colors not matching the map 

        === 

        LEGEND PLACEMENT 

        description: Where on the map the legend is located. 

        options: top left/top center/top right/middle left/center/middle right/bottom left/bottom center/bottom right 

        good: Clear and unobtrusive (usually side or bottom) 

        bad: Obscures map features or hard to locate 

        === 

        BORDER FOR LEGEND 

        description: Whether the legend has a border, and if so, its color. 

        options: yes/no/not applicable 

        === 

        VARIABLES 

        description: The number of distinct data variables represented in the choropleth map. 

        options: <1/2/3/...> 

        good: The variable is clearly identified in the title or legend. 

        bad: The variable is ambiguous or missing. 

        === 

        FREQUENCY 

        description: Indicates whether the frequency (or count) of data points in each category/bin is displayed alongside the categories in the legend or map. 

        options: yes/no 

        === 

        SEMANTIC TYPE 

        description: What real-world value the data represents. 

        examples: population density/rainfall/GDP 

        good: Meaningful and easily identifiable from the map. 

        bad: Arbitrary or unclear semantic type. 

        === 

        BACKGROUND COLOUR 

        description: The color used for the map background (areas outside the data region, e.g., oceans or other continents). 

        good: Neutral and unobtrusive. 

        bad: Distracting or competing with thematic colors. 

        === 

        CLASSIFICATION METHOD 

        description: For discrete data, denotes how the bin intervals were decided. Continuous data are listed as “Unclassed.” If not identifiable, assume “Manual Intervals.” 

        options: Equal Interval/Pretty Breaks/Geometric/Exponential/Quantile/Percentile/Standard Deviation/Maximum Breaks/Unclassed/Manual Intervals 

        good: Method is appropriate for data distribution. 

        bad: Misleading or arbitrary method. 

        === 

        OUTPUT FORMAT 

        { 

        "info": { 

            "map_title": "<map title>", 

            "url": "<url>", 

            "citations": "<citations>", 

            "legend": { 

            "has_legend": "<yes/no>", 

            "orientation": "<horizontal/vertical/other/not applicable>", 

            "range": <range>, 

            "no_data": "<yes/no/not applicable>", 

            "explicit_other": "<yes/no/not applicable>", 

            "incomplete_info": "<yes/no/not applicable>", 

            "data_type": "<nominal/ordinal/ratio/interval>", 

            "contiguity": "<yes/no/not applicable>", 

            "num_bins": <1/2/3/.../'not applicable'>, 

            "colour_scheme": "<colour scheme>", 

            "colours": <colours>, 

            "placement": "<legend placement>", 

            "border": "<border for legend>" 

            }, 

            "variables": <1/2/3/...>, 

            "frequency": "<yes/no>", 

            "semantic_type": "<semantic type>", 

            "bgcolour": "<background colour>", 

            "classification": "<classification method>" 

        }, 

        "explanation": "<Step 4: factually explain the contents of the map within 100 words>", 

        "map_quality": "<Step 6: Evaluate and explain whether the map counts as good or bad in 300 words>" 

        } 

        === 

        ERROR HANDLING 

        If the image input cannot be read, output: “The image cannot be read.” 

        If the image input is not a choropleth map, output: “The image given is not a choropleth map.” 
        
        """


        with OpenRouter(api_key=api_key) as client:
            response = client.chat.send(
                #temp, will use gpt-5o
                model="openai/gpt-4o",
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

        analysis_output = response.choices[0].message.content

        # Store result
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
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)