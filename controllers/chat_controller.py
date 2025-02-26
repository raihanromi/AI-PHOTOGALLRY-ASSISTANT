import uuid
import base64
from pathlib import Path
from db import query_images_based_on_text, query_images_based_on_image
from multimodel.gemini_model import gemini_chat_conversation, gemini_classify_intent, gemini_combine_summary , gemini_image_description
from utils import filter_query_response

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

chat_sessions = {}


def get_or_create_session(session_id: str):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    return chat_sessions[session_id]



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
            image_description = gemini_image_description(file_path)
            merged_prompt = image_description + " " + prompt
            generalized_description = gemini_combine_summary(merged_prompt)
            print(generalized_description)
            query_response = query_images_based_on_text(generalized_description, n_results=5)
            ranked_images = filter_query_response(query_response)
            chat_entry["images"] = ranked_images

        else:
            query_response = query_images_based_on_image(image_content, n_results=5)
            ranked_images = filter_query_response(query_response)
            chat_entry["images"] = ranked_images

        chat_entry["image_query"] = f"/static/uploads/{file_name}"

    elif prompt:
        query_response = query_images_based_on_text(prompt, n_results=10)
        ranked_images = filter_query_response(query_response)
        print(ranked_images)
        chat_entry["images"] = ranked_images

    if chat_entry["images"]:
        image_captions = [image_data["caption"] for image_data in chat_entry["images"]]
        captions_string = ", ".join(image_captions)
        combined_summary = gemini_combine_summary(captions_string)
        chat_entry["combined_summary"] = combined_summary if combined_summary else "No summary available."

    chat_history.append(chat_entry)
    return chat_history


def chatbot(session_id: str, prompt: str, image=None):
    intent = gemini_classify_intent(prompt)
    chat_history = get_or_create_session(session_id)

    if intent == "image_search" or (image and image.size):
        generate_text(session_id, prompt, image)
    else:
        previous_context = "\n".join(
            [f"User: {entry['prompt']}\nBot: {entry['combined_summary']}" for entry in chat_history if
             entry['combined_summary']])
        conversation_prompt = f"You are a helpful assistant. Engage in a conversation with context:\n{previous_context}\nUser: {prompt}" if previous_context else f"You are a helpful assistant. Engage in a conversation: {prompt}"
        response = gemini_chat_conversation(conversation_prompt)
        chat_entry = {"prompt": prompt, "images": [], "image_query": None, "combined_summary": response}
        chat_history.append(chat_entry)

    return chat_history