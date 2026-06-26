from aio_pika import Message
from fastapi import APIRouter, Request, HTTPException, status as HTTPStatus

from app.messaging.messages.base import to_dict
from app.messaging.messages.job_update import JobUpdateMessage
from app.messaging.messages.keywords_match import KeywordsMatchMessage
from app.services.notifications import notification_hub

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/send-job-update", status_code=200)
async def send_job_update_message(message: JobUpdateMessage,  request: Request):
    """
    Endpoint to send a job update message to RabbitMQ.
    """
    rabbitmq_client = request.app.state.rabbitmq

    if not rabbitmq_client and not rabbitmq_client.is_ready:
        raise HTTPException(status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR, detail="RabbitMQ not ready")

    await rabbitmq_client.publish(message)

    return {"status": "ok"}

@router.post("/article-keywords-alert", status_code=200)
async def send_keywords_match_message(message: KeywordsMatchMessage,  request: Request):
    """
    Endpoint to send a keywords match message to RabbitMQ.
    """
    rabbitmq_client = request.app.state.rabbitmq

    if not rabbitmq_client and not rabbitmq_client.is_ready:
        raise HTTPException(status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR, detail="RabbitMQ not ready")

    await rabbitmq_client.publish(message)

    return {"status": "ok"}

@router.post("/send", status_code=200, response_model=dict)
async def send_message(message: dict):
    """Endpoint to send a generic message to the notification hub."""
    await notification_hub.broadcast(
        "keywords_alert", {
            "article_id": "12345",
            "title": message["title"]  if "title" in message else "Sample Article Title",
            "url": "https://example.com",
            "matched_keywords": ["keyword1", "keyword2"],
            "published_at": "2024-06-01T12:00:00Z",
        }
    )
    return { 
                "status": "ok",
                "message" : message["title"]  if "title" in message else "Sample Article Title"
        }


