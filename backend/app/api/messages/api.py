
from tkinter import Message

from fastapi import APIRouter
from ...schemas.messages import Message
from ...services.notifications import notification_hub


router = APIRouter(prefix="/messages", tags=["messages (Dev only)"])


@router.post("/send", status_code=201)
async def send_message(message: Message):
    
    await notification_hub.broadcast(
            "keywords_alert", {
                "article_id": "12345",
                "title": message.message,
                "url": "https://example.com",
                "matched_keywords": ["keyword1", "keyword2"],
                "published_at": "2024-06-01T12:00:00Z",
            }
        )
