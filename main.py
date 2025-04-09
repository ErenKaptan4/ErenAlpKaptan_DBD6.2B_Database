# Import necessary libraries
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Path, Query
from pydantic import BaseModel, Field, ValidationError
import motor.motor_asyncio
from dotenv import load_dotenv
import os
from bson import ObjectId, errors
from typing import List, Optional
import re

# Create the FastAPI application instance
app = FastAPI()

# Load environment variables from .env file
load_dotenv()
getVar = os.getenv("EnvVariable")  # Get MongoDB connection string



def validate_object_id(id_str: str) -> bool:
    """Validate if a string is a valid MongoDB ObjectId."""
    try:
        ObjectId(id_str)  # Attempt to create an ObjectId
        return True
    except (errors.InvalidId, TypeError):
        return False


# Sanitize inputs to prevent NoSQL injection attacks
def sanitize_input(input_str: str) -> str:
    """Sanitize input to prevent NoSQL injection attacks."""
    if not isinstance(input_str, str):
        return input_str
    # Remove MongoDB operators and risky characters
    dangerous_patterns = [
        "$", "{", "}", ".", "$where", "$regex", "$gt", "$lt", "$gte", "$lte",
        "$ne", "$nin", "$and", "$or", "$not", "$nor"
    ]
    result = input_str
    for pattern in dangerous_patterns:
        result = result.replace(pattern, "")  # Remove potentially harmful patterns
    return result


# Validate audio file types - only allow MP3
def is_valid_audio_file(filename: str) -> bool:
    """Check if file is a valid audio file type (MP3 only)."""
    if not filename:
        return False
    return filename.lower().endswith('.mp3')  # Check if file is MP3


# Validate image file types - only allow PNG and JPG/JPEG
def is_valid_image_file(filename: str) -> bool:
    """Check if file is a valid image file type (PNG or JPG/JPEG only)."""
    if not filename:
        return False
    return filename.lower().endswith(('.png', '.jpg', '.jpeg'))  # Check if file is PNG, JPG or JPEG


# --- DATABASE CONNECTION ---

# Create a dependency that provides a database connection
async def get_database():
    client = motor.motor_asyncio.AsyncIOMotorClient(getVar, maxPoolSize=1, minPoolSize=0, serverSelectionTimeoutMS=5000)
    try:
        yield client.multimedia_db  # give the database to do endpoint
    finally:
        client.close()  # close connection


# --- ROOT ENDPOINT ---

# Debugging printing to confirm the server is running
@app.get("/")
async def root():
    return {"message": "Hello World"}  # Simple response to confirm API is working


# --- DATA MODELS ---

# Define the player score data model with validation
class PlayerScore(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z0-9_ ]+$")
    score: int = Field(..., ge=0)  # Score must be >= 0


# --- GET ENDPOINTS ---

# Get a sprite by ID
@app.get("/sprite/{sprite_id}")
async def get_sprite(sprite_id: str, db=Depends(get_database)):
    try:
        # Validate the ObjectId format
        if not validate_object_id(sprite_id):
            raise HTTPException(status_code=400, detail="Invalid sprite ID format")

        # Find the sprite in the database
        sprite = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if sprite:
            return {"filename": sprite["filename"]}  # Return only the filename
        else:
            raise HTTPException(status_code=404, detail="Sprite not found")
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        # Log error printout error
        print(f"Error retrieving sprite: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the sprite")


# Get an audio file by ID
@app.get("/audio/{audio_id}")
async def get_audio(audio_id: str, db=Depends(get_database)):
    try:
        # Validate the ObjectId format
        if not validate_object_id(audio_id):
            raise HTTPException(status_code=400, detail="Invalid audio ID format")

        # Find the audio in the database
        audio = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if audio:
            return {"filename": audio["filename"]}  # Return only the filename
        else:
            raise HTTPException(status_code=404, detail="Audio not found")
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error retrieving audio: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the audio")


# Get player scores with pagination
@app.get("/player_scores", response_model=List[PlayerScore])
async def get_scores(limit: int = Query(10, ge=1, le=100), db=Depends(get_database)):
    try:
        # Retrieve scores from database with limit
        scores = await db.scores.find().limit(limit).to_list(limit)
        # Convert to PlayerScore models, without MongoDB _id field
        return [PlayerScore(**{k: v for k, v in score.items() if k != '_id'}) for score in scores]
    except Exception as e:
        print(f"Error retrieving player scores: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving player scores")


# --- POST ENDPOINTS ---

# Upload a sprite file (PNG/JPG only)
@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Validate file type to ensure only PNG/JPG files are accepted
        if not is_valid_image_file(file.filename):
            raise HTTPException(status_code=400, detail="Only PNG and JPG/JPEG files are allowed")

        # Read file content and store in database
        content = await file.read()
        sprite_doc = {"filename": file.filename, "content": content}
        result = await db.sprites.insert_one(sprite_doc)
        return {"message": "Sprite uploaded", "id": str(result.inserted_id)}
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error uploading sprite: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while uploading the sprite")


# Upload an audio file (MP3 only)
@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Validate file type to ensure only MP3 files are accepted
        if not is_valid_audio_file(file.filename):
            raise HTTPException(status_code=400, detail="Only MP3 files are allowed")

        # Read file content and store in database
        content = await file.read()
        audio_doc = {"filename": file.filename, "content": content}
        result = await db.audio.insert_one(audio_doc)
        return {"message": "Audio file uploaded", "id": str(result.inserted_id)}
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error uploading audio: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while uploading the audio file")


# Add a player score
@app.post("/player_score")
async def add_score(score: PlayerScore, db=Depends(get_database)):
    try:
        # Convert Pydantic model to dict
        score_doc = score.model_dump()
        # Extra sanitization even though Pydantic already validates
        score_doc["player_name"] = sanitize_input(score_doc["player_name"])

        # Insert score into database
        result = await db.scores.insert_one(score_doc)
        return {"message": "Score recorded", "id": str(result.inserted_id)}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))  # Validation errors
    except Exception as e:
        print(f"Error adding player score: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while recording the score")


# --- PUT ENDPOINTS ---

# Update a player's score
@app.put("/player_score/{player_name}")
async def update_score(player_name: str, updated_score: int = Query(..., ge=0), db=Depends(get_database)):
    try:
        # Sanitize input to prevent NoSQL injection
        safe_player_name = sanitize_input(player_name)

        # Update the player's score
        result = await db.scores.update_one(
            {"player_name": safe_player_name},
            {"$set": {"score": updated_score}}
        )

        # Check if player exists
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Player not found")

        return {"message": f"Score updated for player {safe_player_name}"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="Invalid score value")
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error updating score: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while updating the player score")


# Update a sprite file (PNG/JPG only)
@app.put("/sprite/{sprite_id}")
async def update_sprite(sprite_id: str, file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Validate the ObjectId format
        if not validate_object_id(sprite_id):
            raise HTTPException(status_code=400, detail="Invalid sprite ID format")

        # Validate file type to ensure only PNG/JPG files are accepted
        if not is_valid_image_file(file.filename):
            raise HTTPException(status_code=400, detail="Only PNG and JPG/JPEG files are allowed")

        # Check if sprite exists
        sprite = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if not sprite:
            raise HTTPException(status_code=404, detail="Sprite not found")

        # Read file content and update in database
        content = await file.read()
        await db.sprites.update_one(
            {"_id": ObjectId(sprite_id)},
            {"$set": {"filename": file.filename, "content": content}}
        )

        return {"message": "Sprite updated"}
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error updating sprite: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while updating the sprite")


# Update an audio file (MP3 only)
@app.put("/audio/{audio_id}")
async def update_audio(audio_id: str, file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Validate the ObjectId format
        if not validate_object_id(audio_id):
            raise HTTPException(status_code=400, detail="Invalid audio ID format")

        # Validate file type to ensure only MP3 files are accepted
        if not is_valid_audio_file(file.filename):
            raise HTTPException(status_code=400, detail="Only MP3 files are allowed")

        # Check if audio exists
        audio = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if not audio:
            raise HTTPException(status_code=404, detail="Audio not found")

        # Read file content and update in database
        content = await file.read()
        await db.audio.update_one(
            {"_id": ObjectId(audio_id)},
            {"$set": {"filename": file.filename, "content": content}}
        )

        return {"message": "Audio updated"}
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error updating audio: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while updating the audio file")


# --- DELETE ENDPOINTS ---

# Delete a sprite by ID
@app.delete("/sprite/{sprite_id}")
async def delete_sprite(sprite_id: str, db=Depends(get_database)):
    try:
        # Validate the ObjectId format
        if not validate_object_id(sprite_id):
            raise HTTPException(status_code=400, detail="Invalid sprite ID format")

        # Delete the sprite
        result = await db.sprites.delete_one({"_id": ObjectId(sprite_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Sprite not found")
        return {"message": "Sprite deleted"}
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error deleting sprite: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while deleting the sprite")


# Delete an audio file by ID
@app.delete("/audio/{audio_id}")
async def delete_audio(audio_id: str, db=Depends(get_database)):
    try:
        # Validate the ObjectId format
        if not validate_object_id(audio_id):
            raise HTTPException(status_code=400, detail="Invalid audio ID format")

        # Delete the audio
        result = await db.audio.delete_one({"_id": ObjectId(audio_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Audio not found")
        return {"message": "Audio deleted"}
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error deleting audio: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while deleting the audio file")


# Delete a player's score by name
@app.delete("/player_score/{player_name}")
async def delete_score(player_name: str, db=Depends(get_database)):
    try:
        # Sanitize input to prevent NoSQL injection
        safe_player_name = sanitize_input(player_name)

        # Delete the player's score
        result = await db.scores.delete_one({"player_name": safe_player_name})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Player score not found")
        return {"message": f"Score for player {safe_player_name} deleted"}
    except HTTPException as e:
        raise e  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Error deleting score: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while deleting the player score")