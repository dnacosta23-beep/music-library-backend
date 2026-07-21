import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client


# Load variables from the local .env file
load_dotenv()


# Create the Flask application
app = Flask(__name__)


# Get the deployed frontend URL from the environment
frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
).strip().rstrip("/")


# Allow the local and deployed React frontends to communicate with Flask
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
                frontend_url,
            ]
        }
    },
)


# Get the Supabase project URL and publishable key
supabase_url = os.getenv(
    "VITE_SUPABASE_URL",
    "",
).strip().rstrip("/")

supabase_key = os.getenv(
    "VITE_SUPABASE_PUBLISHABLE_KEY",
    "",
).strip()


# Stop the app if the Supabase variables are missing
if not supabase_url or not supabase_key:
    raise RuntimeError(
        "Supabase environment variables are missing."
    )


# Confirm that the Supabase URL has the correct format
if not supabase_url.startswith("https://"):
    raise RuntimeError(
        "The Supabase URL must begin with https://"
    )


if not supabase_url.endswith(".supabase.co"):
    raise RuntimeError(
        "The Supabase URL must end with .supabase.co. "
        f"Current value: {supabase_url}"
    )


# Safe debugging messages
# This prints the URL, but it does not print the secret key
print("Supabase URL loaded:", supabase_url)
print("Supabase key loaded:", bool(supabase_key))
print("Frontend URL loaded:", frontend_url)


# Connect Flask to Supabase
supabase = create_client(
    supabase_url,
    supabase_key,
)


# HOME: Confirm that the API is running
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Music Library API is running."
    }), 200


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
    try:
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

        if not response.data:
            return jsonify({
                "error": "The song could not be created."
            }), 500

        return jsonify(response.data[0]), 201

    except Exception as error:
        app.logger.exception("Unable to create song")

        return jsonify({
            "error": "Unable to create song.",
            "details": str(error),
        }), 500


# UPDATE: Edit an existing song
@app.route("/songs/<int:song_id>", methods=["PUT"])
def update_song(song_id):
    try:
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

        return jsonify(response.data[0]), 200

    except Exception as error:
        app.logger.exception("Unable to update song")

        return jsonify({
            "error": "Unable to update song.",
            "details": str(error),
        }), 500


# DELETE: Remove a song
@app.route("/songs/<int:song_id>", methods=["DELETE"])
def delete_song(song_id):
    try:
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
        }), 200

    except Exception as error:
        app.logger.exception("Unable to delete song")

        return jsonify({
            "error": "Unable to delete song.",
            "details": str(error),
        }), 500


# Run the Flask development server locally
if __name__ == "__main__":
    app.run(debug=True)