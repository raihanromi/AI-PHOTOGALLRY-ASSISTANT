from db import add_images, get_all_images, get_image_by_id, query_images_based_on_image
from db import delete_image_by_id , update_image_description
from multimodel.gemini_model import  gemini_image_analysis
from utils import filter_query_response, convert_to_jpg,enforce_size_limit

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
                    description = analysis.get("description", "No description available")
                    tags = analysis.get("tags", "")
                except Exception as e:
                    print(f"Image analysis failed: {str(e)}")
                    description = "Image analysis failed"
                    tags = ""

                # Store in database
                result = add_images(image_id, image_path, description, tags)
                results.append({"image_id": image_id, "status": "success"})
                print(f"Image {image_id} added successfully")

            except Exception as e:
                print(f"Failed to process file: {str(e)}")
                results.append({"status": "error", "message": str(e)})

        return {"status": "success", "results": results}

    except Exception as e:
        print(f"Upload operation failed: {str(e)}")
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

        print(paginated_images)
        
        return paginated_images, total_pages
    except Exception as e:
        print(f"Error retrieving gallery images: {str(e)}")
        return [], 0


def get_image_details(image_id):
    """
    Get detailed information about a specific image.

    """
    try:
        # Get image data from database
        query_result = get_image_by_id(image_id)

        if not query_result:
            raise ValueError(f"Image with ID {image_id} not found in database")

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
        caption = metadatas.get("caption", "No caption available")

        # Process tags
        string_tags = metadatas.get("tags", "")
        tags = string_tags.split(",") if string_tags else []
        tags = [tag.strip() for tag in tags if tag.strip()]  # Clean tags

        # Construct absolute path to image file
        base_image_dir = os.path.abspath(str(IMAGEDIR))
        image_path = os.path.join(base_image_dir, image_id)

        # Verify image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

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
            print(f"Error finding related images: {str(e)}")
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
        # Re-raise file not found errors
        raise
    except Exception as e:
        print(f"Error getting image details: {str(e)}")
        raise ValueError(f"Failed to retrieve image details: {str(e)}")



def edit_image_description(image_id, new_description):
    """
    Edit the description of an image in the database.

    """
    try:
        print(f"Updating description for image_id: {image_id} to new_description: {new_description}")
        # Update image description in the database
        update_image_description(image_id, new_description)
        print(f"Image {image_id} description updated successfully")
    except Exception as e:
        print(f"Error editing image description: {str(e)}")
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
            print(f"Image {image_id} deleted successfully")
        else:
            print(f"Image file not found: {image_path}")

    except Exception as e:
        print(f"Error deleting image: {str(e)}")
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
                print(f"Failed to remove {image_path}: {str(e)}")

        return {"status": "success", "removed_files": removed_count}

    except Exception as e:
        print(f"Error clearing query images: {str(e)}")
        return {"status": "error", "message": str(e)}