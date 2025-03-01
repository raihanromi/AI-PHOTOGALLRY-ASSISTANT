import json
import os

# Load configuration from JSON file
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

PROMPT = config['PROMPT']
UTILS = config['UTILS']
DB = config['DB']
CHAT = config['CHAT']
GALLERY = config['GALLERY']
IMAGE_CONTROLLER = config['IMAGE_CONTROLLER']
IMAGE_ROUTES = config['IMAGE_ROUTES']  # Added