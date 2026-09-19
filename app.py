from flask import Flask, render_template, request, jsonify
import pickle
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Paths for models
BOOKS_DATA_PATH = "models/books_data.pkl"
TFIDF_VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"
SVD_MODEL_PATH = "models/svd_model.pkl" # To be added later

# Global variables for models
books_df = None
tfidf_vectorizer = None
tfidf_matrix = None
svd_model = None

def load_models():
    global books_df, tfidf_vectorizer, tfidf_matrix, svd_model
    try:
        # Load books data and TF-IDF vectorizer (Python joblib/pickle)
        with open(BOOKS_DATA_PATH, 'rb') as f:
            books_df = pickle.load(f)
        tfidf_vectorizer = joblib.load(TFIDF_VECTORIZER_PATH)
        
        # Compute the TF-IDF matrix for all books on startup for faster inference
        print("Computing TF-IDF matrix...")
        tfidf_matrix = tfidf_vectorizer.transform(books_df['content'])
        print("TF-IDF model loaded successfully.")
    except Exception as e:
        print(f"Content-based models not found or failed to load: {e}")

    try:
        # Load SVD model when available
        with open(SVD_MODEL_PATH, 'rb') as f:
            svd_model = pickle.load(f)
        print("SVD model loaded successfully.")
    except FileNotFoundError:
        print("SVD model not found. Proceeding with content-based recommendations only.")

# Load models on startup
load_models()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        user_input = data.get('query', '')
        
        if not user_input:
            return jsonify({"status": "error", "message": "Query cannot be empty"}), 400

        if books_df is None or tfidf_vectorizer is None or tfidf_matrix is None:
            return jsonify({
                "status": "warning",
                "message": "Models are currently being trained or failed to load. Displaying placeholder recommendations.",
                "recommendations": [
                    {"title": "Placeholder Book 1", "author": "Author A", "score": 0.99},
                    {"title": "Placeholder Book 2", "author": "Author B", "score": 0.95}
                ]
            })

        # Content-Based Filtering using TF-IDF
        # Transform user query
        query_vector = tfidf_vectorizer.transform([user_input])
        
        # Calculate cosine similarity between query and all books
        sim_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Get top 5 recommendations
        top_indices = sim_scores.argsort()[-5:][::-1]
        
        recommendations = []
        for idx in top_indices:
            score = float(sim_scores[idx])
            # Only include if there is some similarity
            if score > 0:
                book = books_df.iloc[idx]
                recommendations.append({
                    "title": book.get('title', 'Unknown Title'),
                    "author": book.get('authors', 'Unknown Author'),
                    "score": score
                })
        
        if not recommendations:
            return jsonify({
                "status": "success",
                "message": "No matching books found.",
                "recommendations": []
            })
            
        status_msg = "success"
        message_txt = "Recommendations generated successfully using TF-IDF."
        
        # Note: When SVD is added, hybrid logic will go here.
        if svd_model is None:
            message_txt += " (SVD model pending)"

        return jsonify({
            "status": status_msg,
            "message": message_txt,
            "recommendations": recommendations
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
