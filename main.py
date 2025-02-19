import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from db import init_db
from routes import image_routes, chat_routes

app = FastAPI()

app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

app.include_router(image_routes.router)
app.include_router(chat_routes.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)