from dataclasses import dataclass


@dataclass(frozen=True)
class OutboxEmail:
    id: int
    to_email: str
    subject: str
    body: str
