from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from controllers import image_controller
from core.constant import IMAGE_ROUTES

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
async def gallery(request: Request, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1)):
    try:
        gallery_images, total_pages = image_controller.get_gallery_images(page, per_page)

        if not gallery_images:
            return templates.TemplateResponse("gallery.html", {
                "request": request,
                "message": IMAGE_ROUTES["GALLERY_NO_IMAGES"],
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
        print(IMAGE_ROUTES["GALLERY_LOG_ERROR"].format(error=str(e)))
        return templates.TemplateResponse("gallery.html", {
            "request": request,
            "message": IMAGE_ROUTES["GALLERY_ERROR"],
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
        return templates.TemplateResponse("image_viewer.html", {"request": request, "error": IMAGE_ROUTES["IMAGE_VIEWER_ERROR"]})


@router.post("/gallery/{image_id}/edit")
async def edit_image_description(request: Request, image_id: str, new_description: str = Form(...)):
    try:
        image_controller.edit_image_description(image_id, new_description)
        return RedirectResponse(url=f"/gallery/{image_id}", status_code=302)
    except Exception as e:
        print(IMAGE_ROUTES["EDIT_LOG_ERROR"].format(error=str(e)))
        return templates.TemplateResponse("image_viewer.html", {"request": request, "error": IMAGE_ROUTES["EDIT_ERROR"]})


@router.post("/gallery/{image_id}/delete")
async def delete_image(request: Request, image_id: str):
    try:
        image_controller.delete_image(image_id)
        return RedirectResponse(url="/gallery", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("image_viewer.html", {"request": request, "error": IMAGE_ROUTES["DELETE_ERROR"]})