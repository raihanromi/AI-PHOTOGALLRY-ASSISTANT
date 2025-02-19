from db import add_images, get_all_images, get_image_by_id, query_images_based_on_text, query_images_based_on_image
from llm import generate_image_caption
from utils import filter_query_response
import os
import glob
import uuid
from pathlib import Path

IMAGEDIR = "images/"
UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def upload_file(files):
    for file in files:
        contents = file.file.read()
        with open(IMAGEDIR + file.filename, "wb") as f:
            f.write(contents)

        caption = generate_image_caption(contents)
        image_id = file.filename
        image_path = IMAGEDIR + file.filename
        result = add_images(image_id, image_path, caption)
    return "Success"

def get_gallery_images():
    query_result = get_all_images()
    if not query_result or not query_result.get("uris") or len(query_result["uris"]) == 0:
        return []

    gallery_images = []
    uris = query_result["uris"][0] if isinstance(query_result["uris"][0], list) else query_result["uris"]
    ids = query_result["ids"][0] if isinstance(query_result["uris"][0], list) else query_result["ids"]

    for image_id, uri in zip(ids, uris):
        gallery_images.append({"image_id": image_id, "uri": uri})

    return gallery_images

def get_image_details(image_id):
    query_result = get_image_by_id(image_id)
    if isinstance(query_result["uris"], list) and isinstance(query_result["uris"][0], list):
        uri = query_result["uris"][0][0]
    elif isinstance(query_result["uris"], list):
        uri = query_result["uris"][0]
    else:
        uri = query_result["uris"]

    metadatas = query_result["metadatas"][0]
    caption = metadatas.get("caption", "No caption available")
    image = {"uri": uri, "caption": caption, "tags": metadatas.get("tags", [])}

    return image

def clear_query_images():
    query_images = glob.glob(str(UPLOAD_DIR / "*.jpg")) + glob.glob(str(UPLOAD_DIR / "*.png"))
    for image in query_images:
        os.remove(image)