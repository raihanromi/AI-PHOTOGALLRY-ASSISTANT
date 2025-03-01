import uuid
from pathlib import Path
from db import query_images_based_on_text, query_images_based_on_image
from llm.gemini_model import ( gemini_chat_conversation, gemini_classify_intent, gemini_combine_summary,
    gemini_image_description, verify_image_similarity )
from core.utils import filter_query_response
from core.constant import CHAT

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

chat_sessions = {}

def get_or_create_session(session_id: str):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    return chat_sessions[session_id]

def generate_text(session_id, prompt, image, n_results):
    chat_history = get_or_create_session(session_id)
    chat_entry = {"prompt": prompt, "images": [], "image_query": None, "combined_summary": None}

    if image and image.size:
        file_ext = image.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / file_name
        image_content = image.file.read()

        with open(file_path, "wb") as f:
            f.write(image_content)

        # image + prompt
        if prompt:
            image_description = gemini_image_description(file_path)
            merged_prompt = image_description + " " + prompt
            generalized_description = gemini_combine_summary(merged_prompt)
            print(generalized_description)
            query_response = query_images_based_on_text(generalized_description, n_results=n_results)
            ranked_images = filter_query_response(query_response)
            filtered_images = [img for img in ranked_images if verify_image_similarity(img["caption"], prompt)]
            chat_entry['images'] = filtered_images

        # image only
        else:
            prompt_image_description = gemini_image_description(file_path)
            query_response = query_images_based_on_image(image_content, n_results=n_results)
            ranked_images = filter_query_response(query_response)
            filtered_images = [img for img in ranked_images if
                               verify_image_similarity(img["caption"], prompt_image_description)]
            chat_entry["images"] = filtered_images

        chat_entry["image_query"] = f"/static/uploads/{file_name}"

    # text only
    elif prompt:
        query_response = query_images_based_on_text(prompt, n_results=n_results)
        ranked_images = filter_query_response(query_response)
        filtered_images = [img for img in ranked_images if verify_image_similarity(img["caption"], prompt)]
        chat_entry["images"] = filtered_images

    if not chat_entry["images"]:
        chat_entry["combined_summary"] = CHAT['NO_MATCHING_IMAGES']

    # Combine image captions into a summary
    if chat_entry["images"]:
        image_captions = [image_data["caption"] for image_data in chat_entry["images"]]
        captions_string = ", ".join(image_captions)
        combined_summary = gemini_combine_summary(captions_string)
        chat_entry["combined_summary"] = combined_summary if combined_summary else CHAT['NO_SUMMARY_AVAILABLE']

    chat_history.append(chat_entry)
    return chat_history


def chatbot(session_id: str, prompt: str, image=None):
    intent,details = gemini_classify_intent(prompt)
    
    n_results = details.get("number", 5) if details else 5
    modified_prompt = details.get("sentence", "general") if details else "general"

    print(f"Intent: {intent}, Modified Prompt: {modified_prompt}, Number of Results: {n_results}")

    
    chat_history = get_or_create_session(session_id)

    if intent == "image_search" or (image and image.size):
        generate_text(session_id, modified_prompt, image, n_results=n_results)
    else:
        previous_context = "\n".join(
            [f"User: {entry['prompt']}\nBot: {entry['combined_summary']}\nImages: {', '.join([img['caption'] for img in entry['images']])}\nImage Paths: {entry['image_query']}"
             for entry in chat_history if entry['combined_summary']]
        )
        response = gemini_chat_conversation(prompt, previous_context)
        chat_entry = {"prompt": prompt, "images": [], "image_query": None, "combined_summary": response}
        chat_history.append(chat_entry)

    return chat_history