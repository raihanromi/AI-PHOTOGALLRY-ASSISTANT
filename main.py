import json
import uvicorn
from click import prompt
from fastapi import FastAPI, Form, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Depends
from typing import List
from starlette.staticfiles import StaticFiles

from helpers import filter_query_response
from llm import generate_image_caption, generate_object_details, generate_summary_prompt
from db import init_db, add_db, collection, query_images_based_on_image, get_all_images, query_images_based_on_text

app = FastAPI()

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

Depends(dependency=None, use_cache=False)
IMAGEDIR = "images/"
app.mount("/images", StaticFiles(directory=IMAGEDIR), name="images")

init_db()

@app.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload")
async def upload(request: Request):
    return templates.TemplateResponse("upload_images.html", {"request": request})

@app.post("/upload")
async def upload_file(request: Request, files: List[UploadFile] = File(...)):
    for file in files:
        contents = await file.read()
        with open(IMAGEDIR + file.filename, "wb") as f:
            f.write(contents)

        caption = generate_image_caption(contents)

        image_object_details = generate_object_details(contents)

        #print(image_object_details)

        image_id = file.filename
        image_path = IMAGEDIR + file.filename
        result = add_db(image_id, image_path, caption)

        #print(result)
    return RedirectResponse(url="/gallery", status_code=302)



@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    try:
        query_result = get_all_images()

        if not query_result or not query_result.get("uris") or len(query_result["uris"]) == 0:
            return templates.TemplateResponse("gallery.html", {
                "request": request,
                "message": "No images found in the database."
            })

        # Process results
        gallery_images = []
        uris = query_result["uris"][0] if isinstance(query_result["uris"][0], list) else query_result["uris"]
        metadatas = query_result["metadatas"][0] if isinstance(query_result["metadatas"][0], list) else query_result["metadatas"]

        for uri, metadata in zip(uris, metadatas):
            caption = metadata.get("caption", "No caption available") if isinstance(metadata, dict) else "No caption available"
            gallery_images.append({
                "uri": uri,
                "caption": caption
            })

        #print(gallery_images)

        return templates.TemplateResponse("gallery.html", {
            "request": request,
            "images": gallery_images
        })

    except Exception as e:
        print(f"Gallery error: {str(e)}")
        return templates.TemplateResponse("gallery.html", {
            "request": request,
            "message": "An error occurred while loading the gallery."
        })
    
@app.get("/gallery/{image_id}", response_class=HTMLResponse)
async def gallery_image(request: Request, image_id: str):
    return templates.TemplateResponse("gallery_image.html", {"request": request, "image_id": image_id})


@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/generate")
async def generate_text(request: Request, prompt: str = Form(None), image: UploadFile = File(None)):
    if prompt and image.size:
        image_content = await image.read()

        image_description = generate_image_caption(image_content)

        merged_prompt = prompt + " " + image_description

        summarized_prompt = generate_summary_prompt(merged_prompt)
        query_response = query_images_based_on_text(summarized_prompt)

        if not query_response:
            return templates.TemplateResponse("index.html", {"request": request,"message": "No images found in the database."})

        images = filter_query_response(query_response)
        return templates.TemplateResponse("chat.html", {"request": request, "images": images})

    elif prompt:
        query_response = query_images_based_on_text(prompt)
        images = filter_query_response(query_response)

        return templates.TemplateResponse("chat.html", {"request": request, "images": images})

    elif image.size:
        content = await image.read()
        query_response = query_images_based_on_image(content)
        images = filter_query_response(query_response)

        return templates.TemplateResponse("chat.html", {"request": request, "images": images})

    else:
        return templates.TemplateResponse("chat.html", {"request": request, "message": "No prompt or image provided"})



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)