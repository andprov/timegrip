from timegrip.application.common.email_config import EmailConfig
from timegrip.infrastructure.env_loader import get_env_value


def load_email_config() -> EmailConfig:
    return EmailConfig(
        host=get_env_value(key="SMTP_HOST"),
        port=int(get_env_value(key="SMTP_PORT", default="465")),
        username=get_env_value(key="SMTP_USERNAME"),
        password=get_env_value(key="SMTP_PASSWORD"),
        use_tls=get_env_value(key="SMTP_USE_TLS", default="True") == "True",
        from_email=get_env_value(key="SMTP_FROM_EMAIL"),
        from_name=get_env_value(key="SMTP_FROM_NAME", default="TimeGrip"),
        sender_backend=get_env_value(
            key="EMAIL_SENDER_BACKEND",
            default="smtp",
        ),
    )
