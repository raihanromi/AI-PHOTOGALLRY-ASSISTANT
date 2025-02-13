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
