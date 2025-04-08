import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
import motor.motor_asyncio
from dotenv import load_dotenv

# Initialize FastAPI application
app = FastAPI()

# Load environment variables from a .env file
load_dotenv()

# Retrieve the environment variable for the database connection string
getVar = os.getenv("EnvVariable")

# Dependency to get a database connection
async def get_database():
    # Create a new MongoDB client for each request
    client = motor.motor_asyncio.AsyncIOMotorClient(
        getVar,  # MongoDB connection string
        maxPoolSize=1,  # Maximum number of connections in the pool
        minPoolSize=0,  # Minimum number of connections in the pool
        serverSelectionTimeoutMS=5000  # Timeout for server selection
    )
    try:
        # Yield the database instance
        yield client.multimedia_db
    finally:
        # Close the client after the request is completed
        client.close()

# Pydantic model for player score data validation
class PlayerScore(BaseModel):
    player_name: str  # Name of the player
    score: int  # Score of the player

# Endpoint to upload a sprite file
@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db=Depends(get_database)):
    # Read the content of the uploaded file
    content = await file.read()
    # Create a document to store in the database
    sprite_doc = {"filename": file.filename, "content": content}
    # Insert the document into the 'sprites' collection
    result = await db.sprites.insert_one(sprite_doc)
    # Return a success message with the inserted document ID
    return {"message": "Sprite uploaded", "id": str(result.inserted_id)}

# Endpoint to upload an audio file
@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), db=Depends(get_database)):
    # Read the content of the uploaded file
    content = await file.read()
    # Create a document to store in the database
    audio_doc = {"filename": file.filename, "content": content}
    # Insert the document into the 'audio' collection
    result = await db.audio.insert_one(audio_doc)
    # Return a success message with the inserted document ID
    return {"message": "Audio file uploaded", "id": str(result.inserted_id)}

# Endpoint to add a player's score
@app.post("/player_score")
async def add_score(score: PlayerScore, db=Depends(get_database)):
    # Convert the Pydantic model to a dictionary
    score_doc = score.dict()
    # Insert the document into the 'scores' collection
    result = await db.scores.insert_one(score_doc)
    # Return a success message with the inserted document ID
    return {"message": "Score recorded", "id": str(result.inserted_id)}