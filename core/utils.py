from PIL import Image
from io import BytesIO
from llm.gemini_model import gemini_image_description, verify_image_similarity
from core.constant import UTILS
import re

def filter_query_response(query_response):
    image_path = query_response['uris'][0]
    metadatas = query_response['metadatas'][0]
    image_ids = query_response['ids'][0]

    images = []
    for _ in range(len(image_path)):
        images.append({
            "image_id": image_ids[_],
            "image_path": image_path[_],
            "caption": metadatas[_]['caption']
        })

    return images

def enforce_size_limit(image_bytes, max_size_kb=100):
    """Ensure the image is under the specified size (default: 100KB), otherwise resize/compress it."""
    max_size_bytes = max_size_kb * 1024

    if len(image_bytes) <= max_size_bytes:
        return image_bytes

    try:
        image = Image.open(BytesIO(image_bytes))
        quality = 90

        while len(image_bytes) > max_size_bytes and quality > 10:
            output = BytesIO()
            image.save(output, format="JPEG", quality=quality)
            image_bytes = output.getvalue()
            quality -= 10  # Reduce quality gradually

        # If still too large, resize the image dimensions iteratively
        while len(image_bytes) > max_size_bytes:
            width, height = image.size
            new_width = int(width * 0.9)  # Reduce width by 10%
            new_height = int(height * 0.9)  # Reduce height by 10%
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            output = BytesIO()
            image.save(output, format="JPEG", quality=quality)
            image_bytes = output.getvalue()

            # Stop if the image becomes too small (e.g., below 100x100 pixels)
            if new_width < 100 or new_height < 100:
                raise ValueError(UTILS['COMPRESSION_FAILURE'])

        return image_bytes
    except Exception as e:
        raise ValueError(f"{UTILS['COMPRESSION_ERROR']}: {str(e)}")

def convert_to_jpg(image_bytes):
    """Convert the image to JPEG format."""
    try:
        image = Image.open(BytesIO(image_bytes))
        output = BytesIO()
        image.convert("RGB").save(output, format="JPEG", quality=85)
        return output.getvalue()
    except Exception as e:
        raise ValueError(f"{UTILS['CONVERSION_ERROR']}: {str(e)}")