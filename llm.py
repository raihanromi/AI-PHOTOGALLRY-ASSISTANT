import base64
import ollama
#
# def get_vision_system_message()->str:
#     system_message_text = '''
# You're an expert image and photo analyzer.
# You are very perceptive in analyzing images and photos.
# You possess excelent vision.
# Do not read any text unless it is the most prominent in the image.
# Your description should be neutral in tone.
# '''
#     return system_message_text
#

def get_object_system_message()->str:
    system_message_text = '''
You're an expert image and photo analyzer.
You are very perceptive in analyzing images and photos.
You possess excelent vision.
Do not read any text unless it is the most prominent in the image.
You should always output your results in this list format, for example:

[
 {'name': 'a detected object', 'description': 'the detected object's description'},
 {'name': 'another detected object', 'description': 'the other detected object's description'}
]

'''
    return system_message_text

def generate_image_caption(image):
    image_base64 = base64.b64encode(image).decode("utf-8")
    full_response = ""
    for response in ollama.generate(model="llava", prompt="Describe this image", images=[image_base64], stream=True):
        print(response["response"], end="", flush=True)
        full_response += response["response"]
    return full_response

def generate_object_details(image):
    image_base64 = base64.b64encode(image).decode("utf-8")
    prompt = get_object_system_message()
    full_response = ""
    for response in ollama.generate(model="llava", prompt=prompt, images=[image_base64], stream=True):
        print(response["response"], end="", flush=True)
        full_response += response["response"]
    return full_response

def generate_summary_prompt(merged_prompt):
    full_response = ""
    for response in ollama.generate(model="llava", prompt="Summarized the prompt so that i can search the image in the vector database : "+merged_prompt,  stream=True):
        print(response["response"], end="", flush=True)
        full_response += response["response"]
    return full_response
