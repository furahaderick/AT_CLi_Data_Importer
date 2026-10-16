import re
from dataclasses import dataclass

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


@dataclass(slots=True)
class User:
    id: str
    name: str
    email: str

    def __post_init__(self):
        if not self.id or not self.id.strip():
            raise ValueError("User ID must be present and non-empty.")

        if not self.name or not self.name.strip():
            raise ValueError("Name must be present and non-empty.")

        if not self.email or not self.email.strip():
            raise ValueError("Email must be present and non-empty.")

        if not EMAIL_REGEX.match(self.email):
            raise ValueError(f"Invalid email format: '{self.email}'")
