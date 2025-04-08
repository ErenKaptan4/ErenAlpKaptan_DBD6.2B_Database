import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
import motor.motor_asyncio
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()
getVar = os.getenv("EnvVariable")

async def get_database():
    # Create a new client for each request
    client = motor.motor_asyncio.AsyncIOMotorClient(
        getVar,
        maxPoolSize=1,
        minPoolSize=0,
        serverSelectionTimeoutMS=5000
    )
    try:
        yield client.multimedia_db
    finally:
        client.close()

# Connect to Mongo Atlas
class PlayerScore(BaseModel):
    player_name: str
    score: int

@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db=Depends(get_database)):
# In a real application, the file should be saved to a storage service
    content =   await file.read()
    sprite_doc = {"filename": file.filename, "content": content}
    result = await db.sprites.insert_one(sprite_doc)
    return {"message": "Sprite uploaded", "id": str(result.inserted_id)}
@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), db=Depends(get_database)):
    content = await file.read()
    audio_doc = {"filename": file.filename, "content": content}
    result = await db.audio.insert_one(audio_doc)
    return {"message": "Audio file uploaded", "id": str(result.inserted_id)}
@app.post("/player_score")
async def add_score(score: PlayerScore, db=Depends(get_database)):
    score_doc = score.dict()
    result = await db.scores.insert_one(score_doc)
    return {"message": "Score recorded", "id": str(result.inserted_id)}

@app.get("/sprites")
async def get_sprites(db=Depends(get_database)):
    sprites = await db.sprites.find().to_list(100)  # Limit to 100 documents
    return {"sprites": sprites}

@app.get("/audio")
async def get_audio(db=Depends(get_database)):
    audio_files = await db.audio.find().to_list(100)  # Limit to 100 documents
    return {"audio_files": audio_files}

@app.get("/player_scores")
async def get_player_scores(db=Depends(get_database)):
    scores = await db.scores.find().to_list(100)  # Limit to 100 documents
    return {"player_scores": scores}