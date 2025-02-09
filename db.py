import chromadb

# Global client and collection
client = None
collection = None

def init_db():
    global client, collection
    client = chromadb.Client()  # Uses default configuration; adjust if needed.
    # Get or create a collection named "images"
    collection = client.get_or_create_collection("images")

def add_image_embedding(image_id: str, embedding: list):
    global collection
    # For demonstration, we add a document with a dummy text (can be extended with metadata)
    collection.add(
        documents=["placeholder"],  # You could store image metadata or description here.
        embeddings=[embedding],
        ids=[image_id]
    )

def query_images(query_embedding: list, n_results: int = 5):
    global collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    # Expecting results in the form {"ids": [[...]], "distances": [[...]]}
    if results and "ids" in results and results["ids"]:
        return results["ids"][0]  # Return the list of image IDs
    return []
