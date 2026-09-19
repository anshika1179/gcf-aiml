from flask import Flask, render_template, request, jsonify
import pickle
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import surprise

app = Flask(__name__)

# Paths for models
BOOKS_DATA_PATH = "models/books_data.pkl"
TFIDF_VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"
SVD_MODEL_PATH = "models/svd_model.pkl"
BOOKS_DATA_SVD_PATH = "models/books_data_svd.pkl"

# Global variables for models
books_df = None
tfidf_vectorizer = None
tfidf_matrix = None
svd_model = None
title_to_isbn = {}

def load_models():
    global books_df, tfidf_vectorizer, tfidf_matrix, svd_model, title_to_isbn
    try:
        # Load content-based models
        with open(BOOKS_DATA_PATH, 'rb') as f:
            books_df = pickle.load(f)
        tfidf_vectorizer = joblib.load(TFIDF_VECTORIZER_PATH)
        
        print("Computing TF-IDF matrix...")
        tfidf_matrix = tfidf_vectorizer.transform(books_df['content'])
        print("TF-IDF models loaded successfully.")
    except Exception as e:
        print(f"Content-based models not found or failed to load: {e}")

    try:
        # Load collaborative models
        svd_model = joblib.load(SVD_MODEL_PATH)
        with open(BOOKS_DATA_SVD_PATH, 'rb') as f:
            books_data_svd = pickle.load(f)
            
        # Build a title to ISBN mapping for hybrid crossover
        for _, row in books_data_svd.iterrows():
            t = str(row.get('Book-Title', '')).lower().strip()
            if t and t not in title_to_isbn:
                title_to_isbn[t] = row.get('ISBN')
                
        print("SVD models loaded successfully.")
    except Exception as e:
        print(f"SVD model not found or failed to load: {e}")

# Load models on startup
load_models()

def get_fallback_recommendations(user_input):
    query_lower = user_input.lower().strip()
    
    curated_database = [
        {"title": f"The Secrets of {user_input.capitalize()}", "author": "J.K. Rowling", "score": 0.98, "cover": "https://covers.openlibrary.org/b/id/10521270-M.jpg"},
        {"title": "The Hobbit", "author": "J.R.R. Tolkien", "score": 0.95, "cover": "https://covers.openlibrary.org/b/id/12002570-M.jpg"},
        {"title": "To Kill a Mockingbird", "author": "Harper Lee", "score": 0.92, "cover": "https://covers.openlibrary.org/b/id/8225266-M.jpg"},
        {"title": "1984", "author": "George Orwell", "score": 0.90, "cover": "https://covers.openlibrary.org/b/id/7222246-M.jpg"},
        {"title": "Dune", "author": "Frank Herbert", "score": 0.88, "cover": "https://covers.openlibrary.org/b/id/12660086-M.jpg"},
        {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "score": 0.86, "cover": "https://covers.openlibrary.org/b/id/722161-M.jpg"},
        {"title": "Pride and Prejudice", "author": "Jane Austen", "score": 0.85, "cover": "https://covers.openlibrary.org/b/id/8231991-M.jpg"}
    ]
    
    results = []
    for item in curated_database:
        score_boost = 0.05 if query_lower in item['title'].lower() or query_lower in item['author'].lower() else 0.0
        final_score = min(0.99, round(item['score'] + score_boost, 2))
        results.append({
            "title": item['title'],
            "author": item['author'],
            "score": final_score,
            "cover": item['cover']
        })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:5]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        user_input = data.get('query', '')
        user_id = data.get('user_id', 1) # Default user ID if none provided
        
        if not user_input:
            return jsonify({"status": "error", "message": "Query cannot be empty"}), 400

        if books_df is None or tfidf_vectorizer is None or tfidf_matrix is None:
            fallback = get_fallback_recommendations(user_input)
            return jsonify({
                "status": "warning",
                "message": "Model files (.pkl) not found in models/ directory. Displaying fallback recommendations.",
                "recommendations": fallback
            })

        # 1. Content-Based Filtering using TF-IDF
        query_vector = tfidf_vectorizer.transform([user_input])
        sim_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Get top 30 candidates from TF-IDF
        top_indices = sim_scores.argsort()[-30:][::-1]
        
        hybrid_results = []
        
        for idx in top_indices:
            score = float(sim_scores[idx])
            if score > 0:
                book = books_df.iloc[idx]
                title = book.get('title', 'Unknown Title')
                
                # 2. Collaborative Filtering using SVD
                svd_pred = 0
                if svd_model:
                    t_lower = str(title).lower().strip()
                    isbn = title_to_isbn.get(t_lower)
                    if isbn:
                        # Predict rating (usually 1-10 scale for Book-Crossing)
                        svd_pred = svd_model.predict(user_id, isbn).est
                
                # 3. Hybrid scoring
                # Assuming max rating is 10 for normalization
                normalized_svd = svd_pred / 10.0 if svd_pred > 0 else 0
                
                # Weighting: 60% TF-IDF (content match), 40% SVD (user preference)
                # If SVD didn't match an ISBN, it purely relies on TF-IDF
                if normalized_svd > 0:
                    hybrid_score = (score * 0.6) + (normalized_svd * 0.4)
                else:
                    hybrid_score = score
                
                hybrid_results.append({
                    "title": title,
                    "author": book.get('authors', 'Unknown Author'),
                    "score": hybrid_score,
                    "cover": book.get('image_url', '')
                })
        
        # Sort by final hybrid score
        hybrid_results.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = hybrid_results[:5]
        
        if not top_recommendations:
            return jsonify({
                "status": "success",
                "message": "No matching books found.",
                "recommendations": []
            })
            
        status_msg = "success"
        message_txt = "Recommendations generated successfully using Hybrid Model (TF-IDF + SVD)."
        if svd_model is None:
            message_txt = "Recommendations generated successfully using TF-IDF. (SVD model failed to load)"

        return jsonify({
            "status": status_msg,
            "message": message_txt,
            "recommendations": top_recommendations
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
