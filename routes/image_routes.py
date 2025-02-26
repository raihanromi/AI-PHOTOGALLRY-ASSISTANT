from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException,Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from controllers import image_controller

import os
from dotenv import load_dotenv


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
async def gallery(request: Request, page: int = Query(1, ge=1), per_page: int = Query(10, ge=1)):
    try:
        gallery_images, total_pages = image_controller.get_gallery_images(page, per_page)

        if not gallery_images:
            return templates.TemplateResponse("gallery.html", {
                "request": request,
                "message": "No images found in the database.",
                "current_page": page,
                "total_pages": total_pages,
                "per_page": per_page
            })

        return templates.TemplateResponse("gallery.html", {
            "request": request,
            "images": gallery_images,
            "current_page": page,
            "total_pages": total_pages,
            "per_page": per_page
        })
    except Exception as e:
        print(f"Gallery error: {str(e)}")
        return templates.TemplateResponse("gallery.html", {
            "request": request,
            "message": "An error occurred while loading the gallery.",
            "current_page": page,
            "total_pages": 1,
            "per_page": per_page
        })

@router.get("/gallery/{image_id}", response_class=HTMLResponse)
async def gallery_image(request: Request, image_id: str):
    try:
        image = image_controller.get_image_details(image_id)
        return templates.TemplateResponse("image_viewer.html", {"request": request, "image": image, "image_id": image_id, "error": None})
    except Exception as e:
        print(f"Error processing image: {e}")
        return templates.TemplateResponse("image_viewer.html", {"request": request, "error": "Error loading image"})


@router.post("/gallery/{image_id}/edit")
async def edit_image_description(request: Request, image_id: str, new_description: str = Form(...)):
    try:
        print(f"Received request to edit description for image_id: {image_id} with new_description: {new_description}")
        image_controller.edit_image_description(image_id, new_description)
        return RedirectResponse(url=f"/gallery/{image_id}", status_code=302)
    except Exception as e:
        print(f"Error editing image description: {e}")
        return templates.TemplateResponse("image_viewer.html", {"request": request, "error": "Error editing image description"})


@router.post("/gallery/{image_id}/delete")
async def delete_image(request: Request, image_id: str):
    try:
        image_controller.delete_image(image_id)
        return RedirectResponse(url="/gallery", status_code=302)
    except Exception as e:
        print(f"Error deleting image: {e}")
        return templates.TemplateResponse("image_viewer.html", {"request": request, "error": "Error deleting image"})