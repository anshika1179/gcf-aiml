from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np

app = Flask(__name__)

# Paths for models (To be provided later)
TFIDF_MODEL_PATH = "models/tfidf_model.pkl"
SVD_MODEL_PATH = "models/svd_model.pkl"

# Global variables for models
tfidf_model = None
svd_model = None

# We will load models once they are provided
def load_models():
    global tfidf_model, svd_model
    try:
        with open(TFIDF_MODEL_PATH, 'rb') as f:
            tfidf_model = pickle.load(f)
        with open(SVD_MODEL_PATH, 'rb') as f:
            svd_model = pickle.load(f)
        print("Models loaded successfully.")
    except FileNotFoundError:
        print("Models not found. Please place the trained models in the 'models/' directory.")

# Try to load models on startup
load_models()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        user_input = data.get('query', '')
        
        if not tfidf_model or not svd_model:
            return jsonify({
                "status": "warning",
                "message": "Models are currently being trained. Displaying placeholder recommendations.",
                "recommendations": [
                    {"title": "Placeholder Book 1", "author": "Author A", "score": 0.99},
                    {"title": "Placeholder Book 2", "author": "Author B", "score": 0.95},
                    {"title": "Placeholder Book 3", "author": "Author C", "score": 0.88}
                ]
            })

        # Placeholder logic for actual model prediction
        # recommendation_results = generate_hybrid_recommendation(user_input, tfidf_model, svd_model)
        
        return jsonify({
            "status": "success",
            "message": "Recommendations generated successfully.",
            "recommendations": [] # Insert actual results here later
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
