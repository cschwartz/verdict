import factory
from sqlmodel import Session


class BaseModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Base factory for all SQLModel-based factories.

    Subclasses set their own `model` in ``class Meta``.
    The session is injected at test time via ``BaseModelFactory.set_session()``.
    """

    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "flush"

    @classmethod
    def set_session(cls, session: Session) -> None:
        """Bind all factories to the given test session."""
        cls._meta.sqlalchemy_session = session
