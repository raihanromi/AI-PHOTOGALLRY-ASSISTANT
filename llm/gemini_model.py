import google.generativeai as genai
import os
from dotenv import load_dotenv
from core.constant import PROMPT
import json
import PIL.Image
from io import BytesIO

load_dotenv()

# Load API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash')


# Retrieve image description and tags
def gemini_image_analysis(llm_jpg_image):
    try:
        if not llm_jpg_image:
            return {"description": PROMPT['NO_IMAGE_DATA'], "tags": PROMPT['NO_IMAGE_DATA']}

        
        prompt = PROMPT['IMAGE_ANALYSIS_PROMPT']

        image = PIL.Image.open(BytesIO(llm_jpg_image))

        response = model.generate_content([prompt,image])
        text = response.text if hasattr(response, 'text') else PROMPT['NO_ANALYSIS_GENERATED']

        # Parse the response
        desc_start = text.find('[DESCRIPTION]') + 13
        desc_end = text.find('[/DESCRIPTION]')
        tags_start = text.find('[TAGS]') + 6
        tags_end = text.find('[/TAGS]')

        description = text[desc_start:desc_end].strip() if desc_start > 12 and desc_end > desc_start else PROMPT['NO_DESCRIPTION_GENERATED']
        tags = text[tags_start:tags_end].strip() if tags_start > 5 and tags_end > tags_start else PROMPT['NO_TAGS_GENERATED']

        return {"description": description, "tags": tags}

    except Exception as e:
        return {"description": f"{PROMPT['ERROR']}: {str(e)}", "tags": f"{PROMPT['ERROR']}: {str(e)}"}


def gemini_image_description(image_path):
    """Generates a detailed, comprehensive image description using Gemini."""
    try:
        if not image_path:
            return "Unidentified object."

        image = genai.upload_file(image_path)

        # Optimized prompt for detailed and comprehensive descriptions
        prompt = PROMPT['IMAGE_DESCRIPTION_PROMPT']
        response = model.generate_content([prompt, image])

        # Extract and clean response
        raw_response = response.text.strip() if hasattr(response, 'text') else ""

        # Validate and refine response
        if raw_response:
            return raw_response
        else:
            return "Generic object in an unknown setting."

    except Exception as e:
        print(f"Error generating description for {image_path}: {str(e)}")
        return "Unidentified object."



def gemini_chat_conversation(prompt, previous_context):
    try:
        if previous_context:
            conversation_prompt = PROMPT['CHAT_CONVERSATION_PROMPT_WITH_CONTEXT'].format(
                previous_context=previous_context,
                prompt=prompt
            )
        else:
            conversation_prompt = PROMPT['CHAT_CONVERSATION_PROMPT_NO_CONTEXT'].format(
                prompt=prompt
            )

        response = model.generate_content(conversation_prompt)
        generated_text = response.text
        return generated_text
    except Exception as e:
        return f"Error: {str(e)}"


def gemini_generate_summary(prompt):
    refined_prompt = PROMPT['SUMMARIZE_PROMPT'].format(prompt=prompt)
    try:
        response = model.generate_content(refined_prompt)
        generated_text = response.text
        return generated_text
    except Exception as e:
        return f"{PROMPT['ERROR']} {str(e)}"


def gemini_classify_intent(prompt):
    # First check if it's an image search
    if 'PROMPT' not in globals():  # Ensure PROMPT is defined
        raise ValueError("PROMPT dictionary is not defined")

    combine_prompt = PROMPT['CLASSIFY_INTENT_PROMPT'].format(prompt=prompt)

    if 'model' not in globals():  # Ensure model is defined
        raise ValueError("Model is not initialized")

    response = model.generate_content(combine_prompt, generation_config={"temperature": 0.0})

    if "image_search" in response.text.strip().lower():
        try:
            # Create a structured prompt to extract image details
            details_prompt = (
                f"Analyze this request: '{prompt}'\n"
                "Return only a valid object containing:\n"
                '"number": (integer) number of images requested (default to 5 if not specified),\n'
                '"sentence": (string) only the sentence describing the requested image\n'
                'Ensure the response is a valid object, e.g., {"number": 5, "sentence": "a beautiful sunset"}\n'
                'Warning: Dont use backticks (```) in the response, as it will break the JSON format.'
            )

            details_response = model.generate_content(details_prompt, generation_config={"temperature": 0.0})

            details_text = details_response.text.strip()
            
            try:
                details = json.loads(details_text)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {str(e)}")
                details = {"number": 5, "sentence": "general"}

            n_images = details.get("number", 5)
            sentence = details.get("sentence", "general")

            # Always return the valid JSON structure
            return "image_search", {"number": n_images, "sentence": sentence}

        except Exception as e:
            print(f"Error parsing image details: {str(e)}")
            return "image_search", {"number": 5, "sentence": "general"}

    return "chat", None



def gemini_combine_summary(captions_string):
    try:
        prompt = PROMPT['COMBINE_SUMMARY_PROMPT'].format(captions_string=captions_string)
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else PROMPT['NO_SUMMARY_GENERATED']
    except Exception as e:
        return f"Error: {str(e)}"


# verify image similarity with image description
def verify_image_similarity(image_description, prompt):
    try:
        verify_prompt = PROMPT['VERIFY_IMAGE_PROMPT'].format(image_description=image_description,prompt=prompt)
        response = model.generate_content(verify_prompt)
        answer = response.text.strip().lower()
        print(f"Image matches with prompt? : {answer}")
        return "yes" in answer

    except Exception as e:
        return False