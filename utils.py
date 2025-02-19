def filter_query_response(query_response):

    image_path = query_response['uris'][0]
    metadatas = query_response['metadatas'][0]
    images = []
    for _ in range(len(image_path)):
        images.append({
            "image_path": image_path[_],
            "caption": metadatas[_]['caption']
        })

    return images


def dynamic_ranking(query_result, confidence_threshold=1.5):
    # Extract the distances (confidence scores) from the query result
    distances = query_result.get("distances", [])

    # Extract the URIs and metadata

    uris = query_result['uris'][0]
    metadatas = query_result['metadatas'][0]

    # Ensure distances, uris, and metadatas are lists of lists
    if not distances or not uris or not metadatas:
        return []

    # Flatten the lists (assuming they are lists of lists)
    distances = distances[0] if isinstance(distances[0], list) else distances
    uris = uris[0] if isinstance(uris[0], list) else uris
    metadatas = metadatas[0] if isinstance(metadatas[0], list) else metadatas

    # Filter images based on the confidence threshold
    filtered_images = []
    for i, distance in enumerate(distances):
        if distance <= confidence_threshold:  # Lower distance means better match
            filtered_images.append({
                "uri": uris[i],
                "metadata": metadatas[i],
                "distance": distance  # Include distance for debugging
            })

    # Sort filtered images by distance (ascending order)
    filtered_images.sort(key=lambda x: x["distance"])

    return filtered_images


def calculate_dynamic_threshold(distances):
    if not distances:
        return 1.5  # Default threshold if no distances are available

    # Calculate mean and standard deviation of distances
    mean_distance = sum(distances) / len(distances)
    std_dev = (sum((d - mean_distance) ** 2 for d in distances) / len(distances)) ** 0.5

    # Set threshold as mean minus one standard deviation
    dynamic_threshold = mean_distance - std_dev

    return max(dynamic_threshold, 0)  # Ensure threshold is not negative


