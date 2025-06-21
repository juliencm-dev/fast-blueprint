from fastapi import Depends
from .service import EmailService
from server.utils.security import get_token_manager

def get_email_service(token_manager = Depends(get_token_manager)) -> EmailService:
    return EmailService(token_manager = token_manager)

