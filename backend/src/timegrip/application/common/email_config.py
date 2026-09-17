from dataclasses import dataclass


@dataclass
class EmailConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    from_email: str
    from_name: str
    sender_backend: str
