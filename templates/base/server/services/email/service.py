from typing import List, Dict, Any
from pydantic import BaseModel, EmailStr
from pathlib import Path
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType

from server.utils.security.tokens import TokenManager
from server.db.user.schema import User
from server.db.auth.schema import ValidationTokenType
from server.config import settings as s

class EmailSchema(BaseModel):
    email: List[EmailStr]
    subject: str
    body: Dict[str, Any]
    subtype: MessageType

class EmailService:
    def __init__(self, token_manager: TokenManager):
        self._mail = FastMail(self._get_email_config())
        self._token_manager = token_manager


    #NOTE: Public email service methods:

    async def send_validation_email(self, user: User, validation_token_type: ValidationTokenType):
        """Process the user email verification."""
        validation_token = await self._token_manager.create_validation_token(user.id, validation_token_type)
        email_data = self._generate_validation_email_data(user, validation_token, validation_token_type)
        
        async def _send_email(email_data=email_data):
            if validation_token_type == ValidationTokenType.VERIFICATION:
                await self._from_verification_template(email_data)
            else:
                await self._from_password_reset_template(email_data)
        
        return _send_email



    #NOTE: Private email service methods:

    def _generate_validation_email_data(self, user:User, validation_token:str, token_type: ValidationTokenType) -> EmailSchema:
        token_config = {
            ValidationTokenType.VERIFICATION: {
                "subject": "Verify your email address to activate your account",
                "path": "account-activation"
            },
            ValidationTokenType.PASSWORD_RESET: {
                "subject": "Reset your password",
                "path": "reset-password"
            }
        }

        config = token_config[token_type]

        body = {
            "first_name": user.first_name,
            "validation_link": f"http://{s.DOMAIN_URL}{s.API_PREFIX}/auth/{config['path']}/{validation_token}"
        }

        return EmailSchema(
            subject=config["subject"],
            body=body,
            email=[user.email],
            subtype=MessageType.html
        )


    async def _from_verification_template(self, email: EmailSchema):
        message = MessageSchema(
            subject=email.subject,
            template_body=email.body,
            recipients=email.email,
            subtype=email.subtype,
        )
        await self._mail.send_message(message, template_name="verification_email.html")



    async def _from_password_reset_template(self, email: EmailSchema):
        message = MessageSchema(
            subject=email.subject,
            template_body=email.body,
            recipients=email.email,
            subtype=email.subtype,
        )
        await self._mail.send_message(message, template_name="password_reset_email.html")



    #NOTE: Email service configuration builder:

    def _get_email_config(self) -> ConnectionConfig:
        config = ConnectionConfig(
            MAIL_USERNAME = s.MAIL_USERNAME,
            MAIL_PASSWORD = s.MAIL_PASSWORD,
            MAIL_FROM = s.MAIL_FROM,
            MAIL_PORT = s.MAIL_PORT,
            MAIL_SERVER = s.MAIL_SERVER,
            MAIL_FROM_NAME= s.MAIL_FROM_NAME,
            MAIL_STARTTLS = True,
            MAIL_SSL_TLS = False,
            USE_CREDENTIALS = True,
            VALIDATE_CERTS = True,
            TEMPLATE_FOLDER = Path(__file__).parent / 'templates'
        )
        return config
