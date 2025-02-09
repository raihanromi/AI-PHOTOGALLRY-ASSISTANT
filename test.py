import requests
import base64

# Read and encode the image
image_path = r"C:\Users\raiha\Desktop\ML_PROJECT\image_classification\dataset\test\Aaron_Guiel_0001.jpg"
with open(image_path, "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

# Prepare the request payload
data = {
    "model": "llava",
    "prompt": "Describe the image",
    "image": encoded_image
}

# Send the request
response = requests.post("http://localhost:11434/api/generate", json=data)

# Print the response
print(response.text)
