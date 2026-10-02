from sqlalchemy import inspect, text

from database import engine


def main():
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        raise SystemExit("The users table does not exist. Run create_tables.py first.")

    columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" in columns:
        print("users.role already exists; no changes made.")
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE users "
                "ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"
            )
        )

    print("Added users.role with default role 'user'. Existing users preserved.")


if __name__ == "__main__":
    main()