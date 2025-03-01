from db import add_images, get_all_images, get_image_by_id, query_images_based_on_image
from db import delete_image_by_id, update_image_description
from llm.gemini_model import gemini_image_analysis
from core.utils import filter_query_response, convert_to_jpg, enforce_size_limit
from core.constant import  IMAGE_CONTROLLER

import os
import glob
import uuid
from pathlib import Path

# Constants for directory paths
IMAGEDIR = Path("images/")
UPLOAD_DIR = Path("static/uploads")

# Ensure directories exist
IMAGEDIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def upload_file(files):
    """
    Process and upload image files to the storage and vector database.
    """
    results = []

    try:
        for file in files:
            try:
                # Read file data
                image_bytes = file.file.read()

                # Process image
                image_bytes = enforce_size_limit(image_bytes, max_size_kb=100)
                jpg_image = convert_to_jpg(image_bytes)

                # Generate unique ID and path
                image_id = str(uuid.uuid4()) + ".jpg"
                image_path = str(IMAGEDIR / image_id)

                # Save to disk
                with open(image_path, "wb") as f:
                    f.write(jpg_image)

                # Analyze image content
                try:
                    analysis = gemini_image_analysis(image_path)
                    description = analysis.get("description", IMAGE_CONTROLLER["ANALYSIS_DEFAULT_DESCRIPTION"])
                    tags = analysis.get("tags", IMAGE_CONTROLLER["ANALYSIS_DEFAULT_TAGS"])
                except Exception as e:
                    print(IMAGE_CONTROLLER["ANALYSIS_FAIL"].format(error=str(e)))
                    description = IMAGE_CONTROLLER["ANALYSIS_FAIL_DESCRIPTION"]
                    tags = IMAGE_CONTROLLER["ANALYSIS_DEFAULT_TAGS"]

                # Store in database
                result = add_images(image_id, image_path, description, tags)
                results.append({"image_id": image_id, "status": "success"})
                print(IMAGE_CONTROLLER["UPLOAD_SUCCESS"].format(image_id=image_id))

            except Exception as e:
                print(IMAGE_CONTROLLER["UPLOAD_FAIL"].format(error=str(e)))
                results.append({"status": "error", "message": str(e)})

        return {"status": "success", "results": results}

    except Exception as e:
        print(IMAGE_CONTROLLER["UPLOAD_OPERATION_FAIL"].format(error=str(e)))
        return {"status": "error", "message": str(e)}


def get_gallery_images(page=1, per_page=10):
    """
    Retrieve paginated gallery images from the vector database.
    """
    try:
        # Input validation
        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        # Get all images from database
        all_images = get_all_images()

        # Calculate total pages
        total_images = len(all_images)
        total_pages = -(-total_images // per_page)

        # Paginate the sorted images
        start_idx = (page - 1) * per_page
        paginated_images = all_images[start_idx:start_idx + per_page]

        return paginated_images, total_pages
    except Exception as e:
        print(IMAGE_CONTROLLER["GALLERY_ERROR"].format(error=str(e)))
        return [], 0


def get_image_details(image_id):
    """
    Get detailed information about a specific image.
    """
    try:
        # Get image data from database
        query_result = get_image_by_id(image_id)

        if not query_result:
            raise ValueError(IMAGE_CONTROLLER["IMAGE_NOT_FOUND"].format(image_id=image_id))

        # Extract URI with handling for nested lists
        if isinstance(query_result.get("uris", []), list):
            if query_result["uris"] and isinstance(query_result["uris"][0], list):
                uri = query_result["uris"][0][0] if query_result["uris"][0] else ""
            elif query_result["uris"]:
                uri = query_result["uris"][0]
            else:
                uri = ""
        else:
            uri = query_result.get("uris", "")

        # Extract metadata
        metadatas = query_result.get("metadatas", [{}])[0] if query_result.get("metadatas") else {}
        caption = metadatas.get("caption", IMAGE_CONTROLLER["DEFAULT_CAPTION"])

        # Process tags
        string_tags = metadatas.get("tags", "")
        tags = string_tags.split(",") if string_tags else []
        tags = [tag.strip() for tag in tags if tag.strip()]  # Clean tags

        # Construct absolute path to image file
        base_image_dir = os.path.abspath(str(IMAGEDIR))
        image_path = os.path.join(base_image_dir, image_id)

        # Verify image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(IMAGE_CONTROLLER["FILE_NOT_FOUND"].format(image_path=image_path))

        # Read image for similarity search
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Get related images
        try:
            related_images_query_result = query_images_based_on_image(image_bytes)
            related_images = filter_query_response(related_images_query_result)

            # Filter out the current image from related images
            related_images = [img for img in related_images if img.get("image_id") != image_id]
        except Exception as e:
            print(IMAGE_CONTROLLER["RELATED_IMAGES_ERROR"].format(error=str(e)))
            related_images = []

        # Construct response
        image = {
            "uri": uri,
            "caption": caption,
            "tags": tags,
            "related_images": related_images[:5]  # Limit to 5 related images
        }

        return image

    except FileNotFoundError as e:
        raise
    except Exception as e:
        print(IMAGE_CONTROLLER["DETAILS_ERROR"].format(error=str(e)))
        raise ValueError(IMAGE_CONTROLLER["DETAILS_FAIL"].format(error=str(e)))


def edit_image_description(image_id, new_description):
    """
    Edit the description of an image in the database.
    """
    try:
        print(IMAGE_CONTROLLER["EDIT_LOG"].format(image_id=image_id, new_description=new_description))
        # Update image description in the database
        update_image_description(image_id, new_description)
        print(IMAGE_CONTROLLER["EDIT_SUCCESS"].format(image_id=image_id))
    except Exception as e:
        print(IMAGE_CONTROLLER["EDIT_ERROR"].format(error=str(e)))
        raise


def delete_image(image_id):
    """
    Delete an image from the database and storage.
    """
    try:
        # Delete image from database
        delete_image_by_id(image_id)

        # Construct absolute path to image file
        base_image_dir = os.path.abspath(str(IMAGEDIR))
        image_path = os.path.join(base_image_dir, image_id)

        # Verify image exists and delete
        if os.path.exists(image_path):
            os.remove(image_path)
            print(IMAGE_CONTROLLER["DELETE_SUCCESS"].format(image_id=image_id))
        else:
            print(IMAGE_CONTROLLER["DELETE_FILE_NOT_FOUND"].format(image_path=image_path))

    except Exception as e:
        print(IMAGE_CONTROLLER["DELETE_ERROR"].format(error=str(e)))
        raise


def clear_query_images():
    """
    Remove all temporary query images from the upload directory.
    """
    try:
        # Find all image files
        query_images = glob.glob(str(UPLOAD_DIR / "*.jpg")) + glob.glob(str(UPLOAD_DIR / "*.png"))
        removed_count = 0

        # Remove each file
        for image_path in query_images:
            try:
                os.remove(image_path)
                removed_count += 1
            except Exception as e:
                print(IMAGE_CONTROLLER["CLEAR_FAIL"].format(image_path=image_path, error=str(e)))

        return {"status": IMAGE_CONTROLLER["CLEAR_STATUS_SUCCESS"], "removed_files": removed_count}

    except Exception as e:
        print(IMAGE_CONTROLLER["CLEAR_ERROR"].format(error=str(e)))
        return {"status": IMAGE_CONTROLLER["CLEAR_STATUS_ERROR"], "message": str(e)}