import uuid
import base64
from pathlib import Path
from fastapi import HTTPException
from db import query_images_based_on_text, query_images_based_on_image
from utils import filter_query_response, dynamic_ranking, calculate_dynamic_threshold
from llm import ollama, generate_image_caption, generate_summary_prompt

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

chat_sessions = {}


def get_or_create_session(session_id: str):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    return chat_sessions[session_id]


def is_image_request(input_text: str) -> bool:
    keywords = ["image", "show me", "picture", "photo", "visualize", "find me", "look for", "search for"]
    return any(keyword in input_text.lower() for keyword in keywords)


def classify_intent(prompt: str) -> str:
    if is_image_request(prompt):
        return "image_search"
    else:
        return "chat"


def generate_text(session_id, prompt, image):
    chat_history = get_or_create_session(session_id)
    chat_entry = {"prompt": prompt, "images": [], "image_query": None, "combined_summary": None}

    if image and image.size:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / file_name
        image_content = image.file.read()

        with open(file_path, "wb") as f:
            f.write(image_content)

        if prompt:
            image_description = generate_image_caption(image_content)
            generalized_description = generate_summary_prompt(image_description + " " + prompt)
            query_response = query_images_based_on_text(generalized_description, n_result=10)
            distances = query_response.get("distances", [])
            dynamic_threshold = calculate_dynamic_threshold(
                distances[0] if isinstance(distances[0], list) else distances)
            filtered_images = dynamic_ranking(query_response, confidence_threshold=dynamic_threshold)
            chat_entry["images"] = filtered_images

        chat_entry["image_query"] = f"/static/uploads/{file_name}"

    elif prompt:
        query_response = query_images_based_on_text(prompt, n_result=10)
        distances = query_response.get("distances", [])
        dynamic_threshold = calculate_dynamic_threshold(distances[0] if isinstance(distances[0], list) else distances)
        ranked_images = dynamic_ranking(query_response, confidence_threshold=dynamic_threshold)
        chat_entry["images"] = ranked_images

    if chat_entry["images"]:
        image_captions = [image_data['metadata']["caption"] for image_data in chat_entry["images"]]
        captions_string = ", ".join(image_captions)
        combined_summary = ""
        for response in ollama.generate(model="llava",
                                        prompt=f"Summarize the following captions into one clear and concise description: {captions_string}.",
                                        stream=True):
            combined_summary += response["response"]
        chat_entry["combined_summary"] = combined_summary if combined_summary else "No summary available."

    chat_history.append(chat_entry)
    return chat_history


def chatbot(session_id: str, prompt: str, image=None):

    intent = classify_intent(prompt)
    chat_history = get_or_create_session(session_id)

    if intent == "image_search":
        chat_response = generate_text(session_id, prompt, image)
    else:
        conversation_prompt = f"You are a helpful assistant. Engage in a conversation: {prompt}"
        combined_response = ""
        for response in ollama.generate(model="llava", prompt=conversation_prompt, stream=True):
            combined_response += response["response"]
        chat_response = [{"type": "chat", "content": combined_response}]


        chat_entry = {"prompt": prompt, "images": [], "image_query": None, "combined_summary": combined_response}

        chat_history.append(chat_entry)

    return chat_history