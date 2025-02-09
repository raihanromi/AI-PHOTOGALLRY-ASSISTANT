from sentence_transformers import SentenceTransformer
from PIL import Image

# Load the unified CLIP model for both text and images.
# This model supports both modalities and projects them into the same latent space.
model = SentenceTransformer('clip-ViT-B-32')

def get_text_embedding(text: str):
    """
    Compute an embedding for the text using the unified CLIP model.
    """
    embedding = model.encode(text)
    return embedding.tolist()

def get_image_embedding(image: Image.Image):
    """
    Compute an embedding for the image using the same unified CLIP model.
    """
    embedding = model.encode(image)
    return embedding.tolist()
