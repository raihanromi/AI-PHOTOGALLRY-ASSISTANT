# AI Gallery Assistant

## Project Overview

The AI Gallery Assistant is a web application that allows users to upload, organize, and discover images through natural conversations with an AI assistant. The application leverages advanced image recognition and natural language processing to provide intelligent image search and management capabilities.

## Project SceenShot
<img width="942" height="981" alt="Image" src="https://github.com/user-attachments/assets/c82e6b6e-17d1-4481-aca5-2cd7f29a7398" />
<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/4277daed-d50a-4b7b-acd4-a15773039035" />
<img width="1920" height="1080" alt="Image" src="https://github.com/user-attachments/assets/92185e7f-26cd-4721-961e-08f1c2a6b8c4" />

## Project Structure

````
.
├── __pycache__/
├── .env
├── .gitignore
├── .idea/
├── controllers/
│   ├── chat_controller.py
│   ├── image_controller.py
├── core/
│   ├── config.json
│   ├── constant.py
│   ├── utils.py
├── db.py
├── images/
├── llm/
│   ├── gemini_model.py
├── main.py
├── requirements.txt
├── routes/
│   ├── chat_routes.py
│   ├── image_routes.py
├── static/
├── templates/
│   ├── chat.html
│   ├── gallery.html
│   ├── image_viewer.html
│   ├── index.html
│   ├── upload_images.html
├── vector_db/

````


### Key Directories and Files

- **controllers/**: Contains the controllers for handling chat and image-related operations.
  - [`chat_controller.py`](controllers/chat_controller.py ): Manages chat interactions and image queries.
  - [`image_controller.py`](controllers/image_controller.py ): Handles image uploads, retrieval, and management.

- **core/**: Contains core configuration and utility functions.
  - [`config.json`](core/config.json ): Configuration file with various prompts and messages.
  - [`constant.py`](core/constant.py ): Loads and provides access to configuration constants.
  - [`utils.py`](core/utils.py ): Utility functions for image processing and filtering.

- **llm/**: Contains the logic for interacting with the Gemini AI model.
  - [`gemini_model.py`](llm/gemini_model.py ): Functions for generating image descriptions, chat responses, and more.

- **routes/**: Contains the FastAPI route definitions.
  - [`chat_routes.py`](routes/chat_routes.py ): Routes for chat-related endpoints.
  - [`image_routes.py`](routes/image_routes.py ): Routes for image-related endpoints.

- **templates/**: Contains HTML templates for rendering the web pages.
  - [`chat.html`](templates/chat.html ): Template for the chat interface.
  - [`gallery.html`](templates/gallery.html ): Template for the image gallery.
  - [`image_viewer.html`](templates/image_viewer.html ): Template for viewing image details.
  - [`index.html`](templates/index.html ): Template for the home page.
  - [`upload_images.html`](templates/upload_images.html ): Template for the image upload page.

- [`main.py`](main.py ): The main entry point for the FastAPI application.
- [`requirements.txt`](requirements.txt ): Lists the Python dependencies required for the project.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

### Steps

1. **Clone the repository**:
   ```sh
   git clone <repository-url>
   cd <repository-directory>
   
2. **Create a virtual environment:**
```sh
python -m venv .venv
source .venv/bin/activate

```

3. **Install the dependencies**
```sh
pip install -r requirements.txt
```

4. **Set up environment variables: Create a .env file in the project root directory with the following content:**
```sh 
URL="127.0.0.1"
PORT=8000
GEMINI_API_KEY="your-gemini-api-key"
```
5. **Run the application:**

```sh
uvicorn main:app --reload
```

6. **Access the application:** Open your web browser and navigate to `http://127.0.0.1:8000.`
