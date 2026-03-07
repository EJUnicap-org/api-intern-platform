"""Utility script for inserting an initial user into the database.

Usage:
    python seed_user.py --name NAME --email EMAIL

The script will prompt for a password (without echoing) and store a bcrypt-hashed
password in the `users` table.

If the table doesn't yet exist it will be created automatically.
"""
import argparse
import asyncio
import getpass
import sys

import bcrypt

from sqlalchemy.ext.asyncio import AsyncSession

# import the application models and engine
from main import User
from database import engine, Base


async def create_user(name: str, email: str, raw_password: str) -> None:
    hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # ensure tables exist (uses the shared metadata from database.Base)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        user = User(name=name, email=email, hashed_password=hashed)
        session.add(user)
        try:
            await session.commit()
            print(f"user '{email}' successfully created")
        except Exception as exc:  # pragma: no cover - simple utility
            await session.rollback()
            print("failed to create user:", exc)
            sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed first user into the database")
    parser.add_argument("--name", required=True, help="Name of the initial user")
    parser.add_argument("--email", required=True, help="Email address of the initial user")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("passwords do not match", file=sys.stderr)
        sys.exit(1)

    asyncio.run(create_user(args.name, args.email, password))


if __name__ == "__main__":
    main()
