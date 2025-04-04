from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
import motor.motor_asyncio
app = FastAPI()
# Connect to Mongo Atlas
client123 = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://admin:LZEOpvrC4xaEGg7v@erenkaptan.upt8dcm.mongodb.net/?retryWrites=true&w=majority&appName=ErenKaptan")
async def get_database():
    # Create a new client for each request
    try:
        yield client123.multimedia_db
    finally:
        client123.close()

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