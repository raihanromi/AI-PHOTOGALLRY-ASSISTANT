import io
import os
import json
import base64
import requests
import uvicorn
import ollama
from typing import List
from PIL import Image
from fastapi import (
    FastAPI, File, UploadFile, HTTPException, Request, Form, Depends
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import QueryRequest, QueryResponse, ImageUploadResponse
from db import init_db, add_image_embedding, query_images
from embeddings import get_text_embedding, get_image_embedding
from llm import generate_response, generate_caption_for_image



app = FastAPI(title="Conversational Memory Bot API")


Depends(dependency=None , use_cache=False)
IMAGEDIR = "images/"


# Initialize templates
templates = Jinja2Templates(directory="templates")

# Serve static files (for CSS/JS or uploaded images)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Initialize ChromaDB on startup.
init_db()

# In-memory store for image metadata.
# Now each image entry is a dict with "path" and "caption".
image_store = {}

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload_images.html", {"request": request})




@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/chat", response_class=HTMLResponse)
async def process_query(request: Request, query_text: str = Form(...)):
    full_response = ""

    for response in ollama.generate(model="llava", prompt=query_text, stream=True):
        print(response["response"], end="", flush=True)
        full_response += response["response"]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "data": full_response
    })

    # Compute text embedding for the query.
    query_embedding = get_text_embedding(query_text)
    # Retrieve matching images.
    retrieved_ids = query_images(query_embedding)
    # Prepare list of images with captions.
    retrieved_images = [{"id": img_id,
                         "path": "/" + image_store.get(img_id, {}).get("path", ""),
                         "caption": image_store.get(img_id, {}).get("caption", "")}
                        for img_id in retrieved_ids if img_id in image_store]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "query": query_text,
        "response": response_text,
        "images": retrieved_images
    })


@app.get("/related-images/{image_id}")
async def related_images(image_id: str):
    if image_id not in image_store:
        raise HTTPException(status_code=404, detail="Image not found")
    embedding = query_images(get_image_embedding(Image.open(image_store[image_id]["path"])))
    related_images = [{"id": img_id, "path": "/" + image_store[img_id]["path"], "caption": image_store[img_id]["caption"]}
                      for img_id in embedding if img_id in image_store]
    return related_images



@app.post("/upload")
async def upload_file(request: Request, files: List[UploadFile] = File(...)):
    for file in files:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        embedding = get_image_embedding(image)

        image_id = file.filename

        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", image_id)
        with open(file_path, "wb") as f:
            f.write(image_bytes)

            # Generate caption by sending Base64-encoded image to Ollama
            caption = await generate_caption_for_image(image_bytes)

            add_image_embedding(image_id, embedding)  ## TODO : ADD image caption to the chromadb

            image_store[image_id] = {"path": file_path, "caption": caption}


    return templates.TemplateResponse("gallery.html", {"request": request})


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):

    # Prepare image list from the in-memory store.
    images = [{"id": img_id, "path": "/" + meta["path"], "caption": meta["caption"]} for img_id, meta in image_store.items()]
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})


@app.get("/viewer", response_class=HTMLResponse)
async def viewer(request: Request):
    return templates.TemplateResponse("viewer.html", {"request": request})




@app.post("/generate")
async def generate_text(request: Request, prompt: str = Form(...)):

    full_response = ""

    for response in ollama.generate(model="llava", prompt=prompt, stream=True):
        print(response["response"], end="", flush=True)
        full_response += response["response"]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "data": full_response
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

