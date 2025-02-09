import io
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn
from PIL import Image

from models import QueryRequest, QueryResponse, ImageUploadResponse
from db import init_db, add_image_embedding, query_images
from embeddings import get_text_embedding, get_image_embedding
from llm import generate_response, generate_caption_for_image

app = FastAPI(title="Conversational Memory Bot API")

# Enable CORS if needed.
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_image(request: Request, file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        # Compute image embedding (using your unified CLIP model)
        embedding = get_image_embedding(image)
        image_id = file.filename

        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", image_id)
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        add_image_embedding(image_id, embedding)

        # Generate caption by sending Base64-encoded image to Ollama
        caption = await generate_caption_for_image(image_bytes)
        print(caption)


        image_store[image_id] = {"path": file_path, "caption": caption}

        message = f"Image '{image_id}' uploaded successfully! Caption: {caption}"
        return templates.TemplateResponse("upload.html", {"request": request, "message": message})
    except Exception as e:
        return templates.TemplateResponse("upload.html", {"request": request, "message": f"Error: {str(e)}"})


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    """
    Render a gallery page listing all uploaded images with captions.
    """
    # Prepare image list from the in-memory store.
    images = [{"id": img_id, "path": "/" + meta["path"], "caption": meta["caption"]} for img_id, meta in image_store.items()]
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat", response_class=HTMLResponse)
async def process_query(request: Request, query_text: str = Form(...)):

    # Compute text embedding for the query.
    query_embedding = get_text_embedding(query_text)
    # Retrieve matching images.
    retrieved_ids = query_images(query_embedding)
    # Generate a response using LLaVA.
    response_text = generate_response(query_text, retrieved_ids)
    # Prepare list of images with captions.
    retrieved_images = [{"id": img_id,
                         "path": "/" + image_store.get(img_id, {}).get("path", ""),
                         "caption": image_store.get(img_id, {}).get("caption", "")}
                        for img_id in retrieved_ids if img_id in image_store]

    return templates.TemplateResponse("result.html", {
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


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
