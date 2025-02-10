import requests
import base64
import ollama

async def generate_caption_for_image(image_bytes: bytes) -> str:
    # Convert the image bytes to Base64
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    full_response = ""

    for response in ollama.generate(model="llava", prompt="Describe the image",images=[encoded_image], stream=True):
        print(response["response"], end="", flush=True)
        full_response += response["response"]

    return full_response



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