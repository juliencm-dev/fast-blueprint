from fastapi import Depends
from server.utils.security import get_token_manager

from .service import EmailService


def get_email_service(token_manager=Depends(get_token_manager)) -> EmailService:
    return EmailService(token_manager=token_manager)
