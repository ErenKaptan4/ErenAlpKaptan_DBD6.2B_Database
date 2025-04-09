from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel, Field, ValidationError
import motor.motor_asyncio
from dotenv import load_dotenv
import os


# Initialize FastAPI application
app = FastAPI()

# Load environment variables
load_dotenv()
getVar = os.getenv("EnvVariable")

# Dependency to get a database connection
async def get_database():
    client = motor.motor_asyncio.AsyncIOMotorClient(getVar, maxPoolSize=1, minPoolSize=0, serverSelectionTimeoutMS=5000)
    try:
        yield client.multimedia_db
    finally:
        client.close()

# Pydantic model for player score with validation
class PlayerScore(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=50, regex="^[a-zA-Z0-9_ ]+$")  # Alphanumeric and underscores only
    score: int = Field(..., ge=0)  # Score must be a non-negative integer

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Endpoint to upload a sprite file
@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Read the content of the uploaded file
        content = await file.read()
        # Create a document to store in the database
        sprite_doc = {"filename": file.filename, "content": content}
        # Insert the document into the 'sprites' collection
        result = await db.sprites.insert_one(sprite_doc)
        return {"message": "Sprite uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while uploading the sprite.")

# Endpoint to upload an audio file
@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Read the content of the uploaded file
        content = await file.read()
        # Create a document to store in the database
        audio_doc = {"filename": file.filename, "content": content}
        # Insert the document into the 'audio' collection
        result = await db.audio.insert_one(audio_doc)
        return {"message": "Audio file uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while uploading the audio file.")

# Endpoint to add a player's score
@app.post("/player_score")
async def add_score(score: PlayerScore, db=Depends(get_database)):
    try:
        # Validate and sanitize input
        score_doc = score.dict()
        result = await db.scores.insert_one(score_doc)
        return {"message": "Score recorded", "id": str(result.inserted_id)}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")
    #hello