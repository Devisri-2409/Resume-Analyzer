import os
import sys
from sqlalchemy import text
from database import engine

def run_migration():
    sql_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "002_add_verification_and_activity.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split statements by semicolon
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    with engine.begin() as conn:
        for stmt in statements:
            # Skip pure comment lines
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            clean_stmt = "\n".join(lines).strip()
            if not clean_stmt:
                continue
            print(f"Executing: {clean_stmt[:60]}...")
            conn.execute(text(clean_stmt))

    print("Migration 002 applied successfully!")

if __name__ == "__main__":
    run_migration()

