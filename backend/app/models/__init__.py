# Import all models here so SQLAlchemy registers all mappers together.
# Without this, relationship() calls fail with "can't locate a name" errors
# because the referenced model class hasn't been imported yet.
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.session import ChatSession
from app.models.message import Message
from app.models.recommendation import Recommendation
from app.models.profile_history import ProfileHistory

__all__ = [
    "User",
    "StudentProfile",
    "ChatSession",
    "Message",
    "Recommendation",
    "ProfileHistory",
]