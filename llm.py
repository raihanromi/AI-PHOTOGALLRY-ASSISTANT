import base64
import ollama
import re



def generate_image_caption(image):
    image_base64 = base64.b64encode(image).decode("utf-8")
    response = ollama.generate(model="llava", prompt="Image description:", images=[image_base64], stream=False)
    full_response = response["response"]
    return full_response


def generate_image_tags(image):
    image_base64 = base64.b64encode(image).decode("utf-8")
    prompt = "Analyze the given image and generate a concise list of relevant tags that describe its key elements. The tags should be nouns or short phrases, separated by commas, focusing on objects, actions, themes, and colors present in the image."

    response = ollama.generate(model="llava", prompt=prompt, images=[image_base64], stream=False)
    full_response = response["response"]

    # Extracting tags using regex (splitting by comma)
    tags = [tag.strip() for tag in re.split(r',\s*', full_response) if tag]

    return tags

def generate_summary_prompt(merged_prompt):
    refined_prompt = f"Refine this query to be more suitable for searching in the vector database: {merged_prompt}."
    response = ollama.generate(model="llava", prompt=refined_prompt, stream=False)
    return response["response"]