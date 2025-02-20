from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from controllers import image_controller

import os
from dotenv import load_dotenv

load_dotenv()  # Make sure this call happens early
router = APIRouter()
templates = Jinja2Templates(directory="templates")



@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse("upload_images.html", {"request": request})

@router.post("/upload")
async def upload_file(request: Request, files: List[UploadFile] = File(...)):
    image_controller.upload_file(files)
    return RedirectResponse(url="/gallery", status_code=302)

@router.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    try:
        gallery_images = image_controller.get_gallery_images()
        if not gallery_images:
            return templates.TemplateResponse("gallery.html", {"request": request, "message": "No images found in the database."})
        return templates.TemplateResponse("gallery.html", {"request": request, "images": gallery_images})
    except Exception as e:
        print(f"Gallery error: {str(e)}")
        return templates.TemplateResponse("gallery.html", {"request": request, "message": "An error occurred while loading the gallery."})

@router.get("/gallery/{image_id}", response_class=HTMLResponse)
async def gallery_image(request: Request, image_id: str):
    try:
        image = image_controller.get_image_details(image_id)
        print(image)
        return templates.TemplateResponse("image_viewer.html", {"request": request, "image": image, "error": None})
    except Exception as e:
        print(f"Error processing image: {e}")
        return templates.TemplateResponse("image_viewer.html", {"request": request, "error": "Error loading image"})