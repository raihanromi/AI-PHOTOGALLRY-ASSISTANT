import uuid
import base64
from pathlib import Path
from fastapi import HTTPException
from db import query_images_based_on_text, query_images_based_on_image
from utils import filter_query_response, dynamic_ranking ,calculate_dynamic_threshold
from llm import ollama, generate_image_caption, generate_summary_prompt


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
            # TODO: check if the user want to search the image or just chat

            # Generate a description combining image and text prompt
            image_description = generate_image_caption(image_content)
            generalized_description = generate_summary_prompt(image_description + " " + prompt)
            print(generalized_description)

            # Query based on the combined description
            query_response = query_images_based_on_text(generalized_description, n_result=10)
            distances = query_response.get("distances", [])

            # Calculate dynamic threshold
            dynamic_threshold = calculate_dynamic_threshold(
                distances[0] if isinstance(distances[0], list) else distances)
            print(f"Dynamic Threshold: {dynamic_threshold}")

            # Filter images using dynamic ranking
            filtered_images = dynamic_ranking(query_response, confidence_threshold=dynamic_threshold)
            chat_entry["images"] = filtered_images

        chat_entry["image_query"] = f"/static/uploads/{file_name}"

    elif prompt:
        # Query based on text prompt only
        query_response = query_images_based_on_text(prompt, n_result=10)
        distances = query_response.get("distances", [])

        # Calculate dynamic threshold
        dynamic_threshold = calculate_dynamic_threshold(distances[0] if isinstance(distances[0], list) else distances)
        print(f"Dynamic Threshold: {dynamic_threshold}")

        # Filter images using dynamic ranking
        ranked_images = dynamic_ranking(query_response, confidence_threshold=dynamic_threshold)

        print(ranked_images)

        chat_entry["images"] = ranked_images

    # Summarize all retrieved images into one summary using LLaVA
    if chat_entry["images"]:

        try:
            # image_paths = [image_data["uri"] for image_data in chat_entry["images"]]
            # image_bytes_list = []
            #
            # for image_path in image_paths:
            #     with open(image_path, "rb") as f:
            #         image_bytes_list.append(f.read())
            #
            # combined_summary_prompt = "Summarize these images collectively so that I can understand their contextual meaning."
            # encoded_images = [base64.b64encode(image_bytes).decode("utf-8") for image_bytes in image_bytes_list]

            image_captions = [image_data['metadata']["caption"] for image_data in chat_entry["images"]]


            captions_string = ", ".join(image_captions)

            #combined_summary_prompt = "Summarize the given text collectively so that I can understand their contextual meaning."

            # TODO: improve the the combine summary quality

            combined_summary = ""
            for response in ollama.generate(model="llava", prompt=f"Summarize the following captions into one clear and concise description that captures the overall meaning and context of the images: {captions_string}." ,
                                            stream=True):
                combined_summary += response["response"]

            chat_entry["combined_summary"] = combined_summary if combined_summary else "No summary available."
        except Exception as llava_error:
            raise HTTPException(status_code=500,
                                detail=f"Error processing image summarization with the local LLaVA model: {str(llava_error)}")

    print(chat_entry)

    chat_history.append(chat_entry)
    return chat_history