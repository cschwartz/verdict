from typing import Annotated

import typer
from sqlmodel import Session

from app.db import engine
from app.errors import DBError
from app.models.gold_source import GoldSourceType
from app.models.user import RolePublic, User, UserPublic
from app.queries import get_role_by_name, sync_user_roles, upsert_by_gold_source
from app.result import Err, Nothing, Ok, Result, Some

cli = typer.Typer()


def _upsert_local_user(
    session: Session,
    username: str,
    email: str,
) -> Result[UserPublic, DBError]:
    def on_existing(existing: User) -> None:
        existing.username = username
        existing.email = email

    def make_new() -> User:
        return User(
            username=username,
            email=email,
            is_active=True,
            gold_source_type=GoldSourceType.LOCAL_USER,
            gold_source_id=username,
        )

    return upsert_by_gold_source(
        session,
        User,
        GoldSourceType.LOCAL_USER,
        username,
        public_class=UserPublic,
        on_existing=on_existing,
        make_new=make_new,
    )


@cli.command()
def create_user(
    username: str = typer.Option(..., help="Username for the local user"),
    email: str = typer.Option(..., help="Email address for the local user"),
    role: Annotated[
        list[str] | None, typer.Option("--role", help="Role name to assign (repeatable)")
    ] = None,
) -> None:
    """Create a local user, setting its roles to exactly the provided list. Fully idempotent."""
    with Session(engine) as session:
        # Validate all roles up front before modifying anything.
        roles: list[RolePublic] = []
        for role_name in role or []:
            match get_role_by_name(session, role_name, public_class=RolePublic):
                case Err(e):
                    typer.echo(f"Database error: {e.detail}", err=True)
                    raise typer.Exit(code=1)
                case Ok(Some(r)):
                    roles.append(r)
                case Ok(Nothing()):
                    typer.echo(f"Role '{role_name}' not found.", err=True)
                    raise typer.Exit(code=1)

        match _upsert_local_user(session, username, email):
            case Err(e):
                typer.echo(f"Database error: {e.detail}", err=True)
                raise typer.Exit(code=1)
            case Ok(user):
                typer.echo(f"User '{username}' ready.")

        match sync_user_roles(session, user.id, [r.id for r in roles]):
            case Err(e):
                typer.echo(f"Database error: {e.detail}", err=True)
                raise typer.Exit(code=1)
        for rp in roles:
            typer.echo(f"Assigned role '{rp.name}'.")

        session.commit()


if __name__ == "__main__":
    cli()
