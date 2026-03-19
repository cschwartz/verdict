import pytest
import sqlalchemy as sa
from sqlmodel import Session, select
from typer.testing import CliRunner

from app.cli import cli
from app.db import engine
from app.models.gold_source import GoldSourceType
from app.models.user import Role, User, UserRole

runner = CliRunner()

_CLI_USERNAMES = ("cli-user-1", "cli-user-2", "cli-user-3", "cli-user-4", "cli-user-5")
_CLI_ROLES = ("cli-analyst", "cli-viewer")

_userrole_table = UserRole.__table__  # type: ignore[attr-defined]  # SQLModel does not expose __table__ in stubs but it exists on table=True models


def _cleanup(session: Session) -> None:
    """Remove all CLI test users and roles (order matters: links before entities)."""
    for username in _CLI_USERNAMES:
        u = session.exec(
            select(User).where(
                User.gold_source_type == GoldSourceType.LOCAL_USER,
                User.gold_source_id == username,
            )
        ).first()
        if u:
            session.execute(sa.delete(_userrole_table).where(_userrole_table.c.user_id == u.id))
            session.delete(u)
    for role_name in _CLI_ROLES:
        r = session.exec(select(Role).where(Role.name == role_name)).first()
        if r:
            session.execute(sa.delete(_userrole_table).where(_userrole_table.c.role_id == r.id))
            session.delete(r)
    session.commit()


@pytest.fixture(scope="module", autouse=True)
def _seed_roles():
    """Ensure clean state, insert roles needed by CLI tests, clean up after."""
    # Clean up from any prior failed teardown before seeding.
    with Session(engine) as session:
        _cleanup(session)

    with Session(engine) as session:
        session.add(
            Role(
                name="cli-analyst",
                description="",
                gold_source_type=GoldSourceType.IAM_GROUP,
                gold_source_id="cli-gs-analyst",
            )
        )
        session.add(
            Role(
                name="cli-viewer",
                description="",
                gold_source_type=GoldSourceType.IAM_GROUP,
                gold_source_id="cli-gs-viewer",
            )
        )
        session.commit()
    yield
    with Session(engine) as session:
        _cleanup(session)


def test_create_user_succeeds():
    result = runner.invoke(
        cli,
        ["--username", "cli-user-1", "--email", "cli-user-1@example.com"],
    )

    assert result.exit_code == 0
    assert "User 'cli-user-1' ready." in result.output


def test_create_user_is_idempotent():
    first = runner.invoke(
        cli,
        ["--username", "cli-user-2", "--email", "cli-user-2@example.com"],
    )
    assert first.exit_code == 0
    result = runner.invoke(
        cli,
        ["--username", "cli-user-2", "--email", "cli-user-2@example.com"],
    )

    assert result.exit_code == 0
    assert "User 'cli-user-2' ready." in result.output


def test_create_user_with_roles():
    result = runner.invoke(
        cli,
        [
            "--username",
            "cli-user-3",
            "--email",
            "cli-user-3@example.com",
            "--role",
            "cli-analyst",
            "--role",
            "cli-viewer",
        ],
    )

    assert result.exit_code == 0
    assert "Assigned role 'cli-analyst'" in result.output
    assert "Assigned role 'cli-viewer'" in result.output


def test_create_user_role_assignment_is_idempotent():
    first = runner.invoke(
        cli,
        [
            "--username",
            "cli-user-4",
            "--email",
            "cli-user-4@example.com",
            "--role",
            "cli-analyst",
        ],
    )
    assert first.exit_code == 0
    result = runner.invoke(
        cli,
        [
            "--username",
            "cli-user-4",
            "--email",
            "cli-user-4@example.com",
            "--role",
            "cli-analyst",
        ],
    )

    assert result.exit_code == 0


def test_create_user_unknown_role_fails():
    result = runner.invoke(
        cli,
        [
            "--username",
            "cli-user-5",
            "--email",
            "cli-user-5@example.com",
            "--role",
            "nonexistent",
        ],
    )

    assert result.exit_code == 1
