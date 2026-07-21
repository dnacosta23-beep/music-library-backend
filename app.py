import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client


# Load variables from the .env file
load_dotenv()


# Create the Flask application
app = Flask(__name__)


# Allow the React frontend to communicate with Flask
frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
                "https://music-library-frontend.onrender.com",
            ]
        }
    },
)


# Get the Supabase information from environment variables
supabase_url = os.getenv("VITE_SUPABASE_URL", "").strip().rstrip("/")
supabase_key = os.getenv(
    "VITE_SUPABASE_PUBLISHABLE_KEY",
    "",
).strip()


if not supabase_url or not supabase_key:
    raise RuntimeError(
        "Supabase environment variables are missing."
    )


if not supabase_url.startswith("https://"):
    raise RuntimeError(
        "The Supabase URL must begin with https://"
    )


if not supabase_url.endswith(".supabase.co"):
    raise RuntimeError(
        "The Supabase URL must end with .supabase.co. "
        f"Current URL host: {supabase_url}"
    )


print("Supabase URL loaded:", supabase_url)
print("Supabase key loaded:", bool(supabase_key))


supabase = create_client(
    supabase_url,
    supabase_key,
)


# Stop the application if the Supabase variables are missing
if not supabase_url or not supabase_key:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be added to the .env file."
    )


# Connect Flask to Supabase
supabase = create_client(
    supabase_url,
    supabase_key,
)


# Home route
@app.route("/")
def home():
    return jsonify({
        "message": "Music Library API is running."
    })


# READ: Get all songs
@app.route("/songs", methods=["GET"])
def get_songs():
    try:
        response = (
            supabase
            .table("songs")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return jsonify(response.data), 200

    except Exception as error:
        app.logger.exception("Unable to retrieve songs")

        return jsonify({
            "error": "Unable to retrieve songs.",
            "details": str(error),
        }), 500


# CREATE: Add a new song
@app.route("/songs", methods=["POST"])
def add_song():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Song information is required."
        }), 400

    title = data.get("title", "").strip()
    artist = data.get("artist", "").strip()
    genre = data.get("genre", "").strip()
    rating = data.get("rating")

    if not title:
        return jsonify({
            "error": "Title is required."
        }), 400

    if not artist:
        return jsonify({
            "error": "Artist is required."
        }), 400

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Rating must be a number from 1 to 5."
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "error": "Rating must be between 1 and 5."
        }), 400

    new_song = {
        "title": title,
        "artist": artist,
        "genre": genre,
        "rating": rating,
    }

    response = (
        supabase
        .table("songs")
        .insert(new_song)
        .execute()
    )

    return jsonify(response.data[0]), 201


# UPDATE: Edit an existing song
@app.route("/songs/<int:song_id>", methods=["PUT"])
def update_song(song_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Updated song information is required."
        }), 400

    title = data.get("title", "").strip()
    artist = data.get("artist", "").strip()
    genre = data.get("genre", "").strip()
    rating = data.get("rating")

    if not title:
        return jsonify({
            "error": "Title is required."
        }), 400

    if not artist:
        return jsonify({
            "error": "Artist is required."
        }), 400

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Rating must be a number from 1 to 5."
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "error": "Rating must be between 1 and 5."
        }), 400

    updated_song = {
        "title": title,
        "artist": artist,
        "genre": genre,
        "rating": rating,
    }

    response = (
        supabase
        .table("songs")
        .update(updated_song)
        .eq("id", song_id)
        .execute()
    )

    if not response.data:
        return jsonify({
            "error": "Song not found."
        }), 404

    return jsonify(response.data[0])


# DELETE: Remove a song
@app.route("/songs/<int:song_id>", methods=["DELETE"])
def delete_song(song_id):
    response = (
        supabase
        .table("songs")
        .delete()
        .eq("id", song_id)
        .execute()
    )

    if not response.data:
        return jsonify({
            "error": "Song not found."
        }), 404

    return jsonify({
        "message": "Song deleted successfully."
    })


# Run the Flask development server
if __name__ == "__main__":
    app.run(debug=True)

