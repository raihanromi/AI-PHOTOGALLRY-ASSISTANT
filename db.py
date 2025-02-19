import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from PIL import Image
import numpy as np
import io

db = None
collection = None


def init_db():
    global db
    global collection

    print("Initializing database...")  # Debugging line

    try:
        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        db = chromadb.PersistentClient(path="vector_db")
        collection = db.get_or_create_collection("vector_collection", embedding_function=embedding_function,
                                                 data_loader=image_loader)

        if collection:
            print("Database collection initialized successfully.")
        else:
            print("Failed to initialize the database collection.")
    except Exception as e:
        print(f"Error during database initialization: {e}")


def add_images(image_id, image_path, caption=None):
    global collection
    global db

    try:
        collection.add(
            ids=[image_id],
            uris=[image_path],
            metadatas=[{"caption": caption}]
        )
        print(f"Added image {image_id} to the collection.")
        return "Success"
    except Exception as e:
        print(f"Error adding to DB: {e}")
        return "Failure"



def get_all_images():
    global collection
    query_result = collection.get(
        include=["uris", "metadatas"]
    )

    return query_result

def get_image_by_id(image_id):
    query_result = collection.get(
        ids = [image_id],
        include=["uris", "metadatas"]
    )
    return query_result

def query_images_based_on_text(query_text, n_result=10):
    global collection

    query_result = collection.query(
        query_texts=[query_text],
        n_results=n_result,
        include=["uris", "metadatas", "distances"]  # Include distances (confidence scores)
    )

    return query_result

def query_images_based_on_image(image, n_results=10):
    global collection

    pil_image = Image.open(io.BytesIO(image))
    np_image = np.array(pil_image)

    query_result = collection.query(
        query_images=[np_image],
        n_results=n_results,
        include=["uris", "metadatas", "distances"]  # Include distances (confidence scores)
    )

    return query_result

