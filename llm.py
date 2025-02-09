import json

import requests
import base64
import httpx

async def generate_caption_for_image(image_bytes: bytes) -> str:
    """
    Generate a caption for the given image bytes using the locally hosted Ollama endpoint.
    """
    url = "http://localhost:11434/api/generate"  # Adjust this endpoint as needed.
    headers = {"Content-Type": "application/json"}

    # Convert the image bytes to Base64
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": "llava",
        "prompt": "Describe the image",
        "image": encoded_image,
        "stream":False
    }


    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "No caption provided from Ollama.")

def generate_response(query_text: str, image_ids: list) :
    """
    Generate a response using the locally hosted LLaVA chat endpoint.

    This function sends a JSON payload containing the query text and image IDs to LLaVA.
    """

    url = "http://localhost:11434/api/generate"  # Adjust this endpoint as needed.
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": "llava",
        "query": query_text,
        "stream":False
    }
    try:
        response = requests.post(url,  headers=headers,json=payload)
        print(response.text)
        response.raise_for_status()
        data = response.json()
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error calling LLaVA: {e}"