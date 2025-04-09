from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Path, Query
from pydantic import BaseModel, Field, ValidationError
import motor.motor_asyncio
from dotenv import load_dotenv
import os
from bson import ObjectId
from typing import List, Optional

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

#testing if vercel works properly
@app.get("/")
async def root():
    return {"message": "Hello World"}


class PlayerScore(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z0-9_ ]+$")
    score: int = Field(..., ge=0)


# GET endpoints
@app.get("/sprite/{sprite_id}")
async def get_sprite(sprite_id: str, db=Depends(get_database)):
    try:
        sprite = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if sprite:
            # Convert binary data to base64 if needed for frontend display
            return {"filename": sprite["filename"]}
        else:
            raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audio/{audio_id}")
async def get_audio(audio_id: str, db=Depends(get_database)):
    try:
        audio = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if audio:
            return {"filename": audio["filename"]}
        else:
            raise HTTPException(status_code=404, detail="Audio not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/player_scores", response_model=List[PlayerScore])
async def get_scores(limit: int = Query(10, ge=1, le=100), db=Depends(get_database)):
    try:
        scores = await db.scores.find().limit(limit).to_list(limit)
        return [PlayerScore(**{k: v for k, v in score.items() if k != '_id'}) for score in scores]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/player_score/{player_name}")
async def get_player_score(player_name: str, db=Depends(get_database)):
    try:
        score = await db.scores.find_one({"player_name": player_name})
        if score:
            return {**score, "_id": str(score["_id"])}
        else:
            raise HTTPException(status_code=404, detail="Player score not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# POST endpoints (fixed)
@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...), db=Depends(get_database)):
    try:
        content = await file.read()
        sprite_doc = {"filename": file.filename, "content": content}
        result = await db.sprites.insert_one(sprite_doc)
        return {"message": "Sprite uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), db=Depends(get_database)):
    try:
        content = await file.read()
        audio_doc = {"filename": file.filename, "content": content}
        result = await db.audio.insert_one(audio_doc)
        return {"message": "Audio file uploaded", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/player_score")
async def add_score(score: PlayerScore, db=Depends(get_database)):
    try:
        score_doc = score.model_dump()  # Updated from dict() to model_dump()
        result = await db.scores.insert_one(score_doc)
        return {"message": "Score recorded", "id": str(result.inserted_id)}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PUT endpoints
@app.put("/player_score/{player_name}")
async def update_score(player_name: str, updated_score: int = Query(..., ge=0), db=Depends(get_database)):
    try:
        result = await db.scores.update_one(
            {"player_name": player_name},
            {"$set": {"score": updated_score}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Player not found")

        return {"message": f"Score updated for player {player_name}"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/sprite/{sprite_id}")
async def update_sprite(sprite_id: str, file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Check if sprite exists
        sprite = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if not sprite:
            raise HTTPException(status_code=404, detail="Sprite not found")

        # Update sprite
        content = await file.read()
        result = await db.sprites.update_one(
            {"_id": ObjectId(sprite_id)},
            {"$set": {"filename": file.filename, "content": content}}
        )

        return {"message": "Sprite updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/audio/{audio_id}")
async def update_audio(audio_id: str, file: UploadFile = File(...), db=Depends(get_database)):
    try:
        # Check if audio exists
        audio = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if not audio:
            raise HTTPException(status_code=404, detail="Audio not found")

        # Update audio
        content = await file.read()
        result = await db.audio.update_one(
            {"_id": ObjectId(audio_id)},
            {"$set": {"filename": file.filename, "content": content}}
        )

        return {"message": "Audio updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE endpoints
@app.delete("/sprite/{sprite_id}")
async def delete_sprite(sprite_id: str, db=Depends(get_database)):
    try:
        result = await db.sprites.delete_one({"_id": ObjectId(sprite_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Sprite not found")
        return {"message": "Sprite deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/audio/{audio_id}")
async def delete_audio(audio_id: str, db=Depends(get_database)):
    try:
        result = await db.audio.delete_one({"_id": ObjectId(audio_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Audio not found")
        return {"message": "Audio deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/player_score/{player_name}")
async def delete_score(player_name: str, db=Depends(get_database)):
    try:
        result = await db.scores.delete_one({"player_name": player_name})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Player score not found")
        return {"message": f"Score for player {player_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))