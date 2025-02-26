from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from PIL import Image
from datetime import datetime
import chromadb
import numpy as np
import io


db = None
collection = None

def init_db():
    """Initialize the ChromaDB database and collection."""
    global db, collection
    print("Initializing database...")

    try:
        embedding_function = OpenCLIPEmbeddingFunction()
        image_loader = ImageLoader()

        # Establish a persistent database connection
        db = chromadb.PersistentClient(path="vector_db")
        collection = db.get_or_create_collection(
            "vector_collection",
            embedding_function=embedding_function,
            data_loader=image_loader
        )

        if collection:
            print("Collection initialized successfully")
        else:
            print("Failed to initialize collection")
    except Exception as e:
        print(f"Error during database initialization: {e}")

def add_images(image_id, image_path, caption=None, tags=None):
    """Add an image to the database with metadata."""
    global collection
    try:
        created_at = datetime.utcnow().isoformat()

        collection.add(
            ids=[image_id],
            uris=[image_path],
            metadatas=[{"caption": caption, "tags": tags, "created_at": created_at}]
        )
        return "Success"
    except Exception as e:
        print(f"Error adding image to DB: {e}")
        return "Failure"

def get_all_images():
    """Retrieve all images from the database."""
    global collection
    try:
        results = collection.get(
            include=['uris', 'metadatas']
        )

        # Extract and sort images by created_at in descending order
        images = [
            {
                "uri": uri,
                "metadata": metadata,
                "image_id":image_id
            }
            for uri, metadata,image_id in zip(results["uris"], results["metadatas"],results['ids'])
        ]
        images.sort(key=lambda x: x["metadata"]["created_at"], reverse=True)

        return images
    except Exception as e:
        print(f"Error retrieving images: {e}")
        return []
    
    

def get_image_by_id(image_id):
    """Retrieve a specific image by its ID."""
    global collection
    try:
        query_result = collection.get(
            ids=[image_id],
            include=["uris", "metadatas"]
        )
        return query_result
    except Exception as e:
        print(f"Error retrieving image by ID: {e}")
        return None

def query_images_based_on_text(query_text, n_results=10):
    global collection

    query_result = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["uris", "metadatas", "distances"]
    )

    return query_result

def query_images_based_on_image(image, n_results=10):
    global collection

    pil_image = Image.open(io.BytesIO(image))
    np_image = np.array(pil_image)

    query_result = collection.query(
        query_images=[np_image],
        n_results=n_results,
        include=["uris", "metadatas", "distances"]
    )

    return query_result


def delete_image_by_id(image_id):
    """Delete an image from the database by its ID."""
    global collection
    try:
        collection.delete(ids=[image_id])
        print(f"Image {image_id} deleted from database")
    except Exception as e:
        print(f"Error deleting image from DB: {e}")

def update_image_description(image_id, new_description):
    """Update the description of an image in the database."""
    global collection
    try:
        print(f"Updating database for image_id: {image_id} with new_description: {new_description}")
        collection.update(
            ids=[image_id],
            metadatas=[{"caption": new_description}]
        )
        print(f"Image {image_id} description updated in database")
    except Exception as e:
        print(f"Error updating image description in DB: {e}")
        raise