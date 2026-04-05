# models/link.py
import secrets
from peewee import CharField, BooleanField

from app.database import BaseModel

_CODE_BYTES = 5  # 5 bytes = 8 base32 chars, ~1B combinations


class Link(BaseModel):
    """
    Represents a shortened URL.

    - `code` has a unique constraint enforced at the DB level (not just app level).
      This is the correct defense-in-depth approach: app logic generates unique codes,
      but the DB constraint is the final safety net against races.
    - `active` flag allows soft-deletion without breaking referential integrity.
      A deactivated link returns 410 Gone, not 404, so clients can distinguish
      "never existed" from "was removed".
    """
    url = CharField(max_length=2048)
    code = CharField(max_length=12, unique=True)
    active = BooleanField(default=True)

    class Meta:
        table_name = "links"

    @classmethod
    def generate_code(cls) -> str:
        """
        Generates a cryptographically random, URL-safe short code.
        Uses secrets module (CSPRNG), not random (PRNG).
        Retries up to 5 times on collision (astronomically rare but handled).
        """
        for _ in range(5):
            # base32 gives alphanumeric chars only — no padding, URL-safe
            code = secrets.token_urlsafe(_CODE_BYTES)[:8]
            if not cls.select().where(cls.code == code).exists():
                return code
        raise RuntimeError("Failed to generate a unique short code after 5 attempts")