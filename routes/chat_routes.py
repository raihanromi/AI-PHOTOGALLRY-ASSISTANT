from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from controllers import chat_controller
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    session_id = request.cookies.get("chat_session")
    if not session_id:
        session_id = str(uuid.uuid4())

    chat_history = chat_controller.get_or_create_session(session_id)
    response = templates.TemplateResponse("chat.html", {"request": request, "chat_history": chat_history})

    if not request.cookies.get("chat_session"):
        response.set_cookie(key="chat_session", value=session_id)

    return response

@router.post("/generate")
async def generate_text(request: Request, prompt: str = Form(None), image: UploadFile = File(None)):
    session_id = request.cookies.get("chat_session", str(uuid.uuid4()))
    chat_response = chat_controller.chatbot(session_id, prompt, image)
    #print("chat response: ",chat_response)
    response = templates.TemplateResponse("chat.html", {"request": request, "chat_history": chat_response})
    response.set_cookie(key="chat_session", value=session_id)
    return response