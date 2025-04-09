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

@app.get("/")
async def root():
    return {"message": "Hello World"}
#hi

class PlayerScore(BaseModel):
    player_name: str
    score: int
@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db = Depends(get_database)):
    # In a real application, the file should be saved to a storage service
    content = await file.read()
    sprite_doc = {"filename": file.filename, "content": content}
    result = await db.sprites.insert_one(sprite_doc)
    return {"message": "Sprite uploaded", "id": str(result.inserted_id)}
@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), db = Depends(get_database)):
    content = await file.read()
    audio_doc = {"filename": file.filename, "content": content}
    result = await db.audio.insert_one(audio_doc)
    return {"message": "Audio file uploaded", "id": str(result.inserted_id)}
@app.post("/player_score")
async def add_score(score: PlayerScore, db = Depends(get_database)):
    score_doc = score.dict()
    result = await db.scores.insert_one(score_doc)
    return {"message": "Score recorded", "id": str(result.inserted_id)}
