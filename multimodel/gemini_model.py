import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Load API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash')


def gemini_image_analysis(image_path):
    try:
        if not image_path:
            return {"description": "Error: No image data provided.", "tags": "Error: No image data provided."}

        image = genai.upload_file(image_path)
        prompt = '''Analyze the provided image and generate a detailed description followed by a list of relevant tags. 
                    Format the response as: 
                    [DESCRIPTION]description text here[/DESCRIPTION]
                    [TAGS]tag1, tag2, tag3[/TAGS]'''

        response = model.generate_content([prompt, image])
        text = response.text if hasattr(response, 'text') else "No analysis generated."

        # Parse the response
        desc_start = text.find('[DESCRIPTION]') + 13
        desc_end = text.find('[/DESCRIPTION]')
        tags_start = text.find('[TAGS]') + 6
        tags_end = text.find('[/TAGS]')

        description = text[desc_start:desc_end].strip() if desc_start > 12 and desc_end > desc_start else "No description generated."
        tags = text[tags_start:tags_end].strip() if tags_start > 5 and tags_end > tags_start else "No tags generated."

        return {"description": description, "tags": tags}

    except Exception as e:
        return {"description": f"Error: {str(e)}", "tags": f"Error: {str(e)}"}


def gemini_image_description(image_path):
    """Generates a detailed, comprehensive image description using Gemini."""
    try:
        if not image_path:
            print("Error: No image data provided.")
            return "Unidentified object."

        image = genai.upload_file(image_path)

        # Optimized prompt for detailed and comprehensive descriptions
        prompt = (
            "Analyze the provided image and generate a detailed description of everything about the image. "
            "Include information about objects, actions, settings, colors, emotions, and any other relevant details. "
            "Ensure the response is thorough and covers all aspects of the image."
        )
        response = model.generate_content([prompt, image])

        # Extract and clean response
        raw_response = response.text.strip() if hasattr(response, 'text') else ""
        print(f"Raw description response for {image_path}: '{raw_response}'")

        # Validate and refine response
        if raw_response:
            return raw_response
        else:
            print("Description too vague or not generated; using fallback.")
            return "Generic object in an unknown setting."

    except Exception as e:
        print(f"Error generating description for {image_path}: {str(e)}")
        return "Unidentified object."


def gemini_image_tags(image_path):
    """Generates an image caption using Gemini."""
    try:
        # Ensure input is valid
        if not image_path:
            return "Error: No image data provided."
        image = genai.upload_file(image_path)

        prompt = '''Analyze the given image and generate a concise list of relevant tags that describe
              its key elements. The tags should be nouns or short phrases, separated by commas, 
              focusing on objects, actions, themes, and colors present in the image.'''

        response = model.generate_content([prompt, image])

        # Extract and return the text response
        return response.text if hasattr(response, 'text') else "No tags generated."

    except Exception as e:
        return f"Error: {str(e)}"


def gemini_chat_conversation(prompt):
    try:
        response = model.generate_content(prompt)
        generated_text = response.text
        return generated_text

    except Exception as e:
        return f"Error: {str(e)}"


def gemini_generate_summary(prompt):
    refined_prompt = f"Provide a concise text summary . Avoid extra words : {prompt}"
    try:
        response = model.generate_content(refined_prompt)
        generated_text = response.text
        return generated_text
    except Exception as e:
        return f"Error: {str(e)}"


def gemini_classify_intent(prompt):
    try:
        combine_prompt = (
            f"Analyze this prompt: '{prompt}'. "
            "If the user is asking for an image, return exactly 'image_search'. "
            "Otherwise, return exactly 'chat'. "
            "Do not include anything else in the response."
        )

        response = model.generate_content(combine_prompt, generation_config={"temperature": 0.0})
        retrieved_text = response.text.strip().lower()

        if "image_search" in retrieved_text:
            return "image_search"
        elif "chat" in retrieved_text:
            return "chat"
        else:
            return "Error: Unexpected response"
    except Exception as e:
        return f"Error: {str(e)}"


def gemini_combine_summary(captions_string):
    try:
        prompt = f"Summarize the following captions into one short description: {captions_string}."
        response = model.generate_content(prompt)
        return response.text if hasattr(response, 'text') else "No summary generated."
    except Exception as e:
        return f"Error: {str(e)}"


def verify_image_similarity(image_path, prompt):
    try:

        image_description = gemini_image_description(image_path)

        verify_prompt = (
            f"if the {image_description} is similar to the {prompt} , return yes. Otherwise, return no. "

        )
        image_upload = genai.upload_file(image_path)
        response = model.generate_content(verify_prompt)
        answer = response.text.strip().lower()
        print(f"Image {image_path}: Matches '{prompt}'? {answer}")
        return "yes" in answer
    except Exception as e:
        print(f"Error verifying image {image_path}: {str(e)}")
        return False