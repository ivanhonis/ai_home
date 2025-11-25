import sys
import json
import psycopg2
from psycopg2.extras import DictCursor
from pathlib import Path
from typing import Optional, Any

# --- CONFIGURATION ---
VECTOR_DIMENSIONS = 768  # Dimension of Google text-embedding-005
TABLE_NAME = "memories"

# List of expected columns for validation
EXPECTED_COLUMNS = {
    "id",
    "room_id",
    "model_version",
    "essence",
    "dominant_emotions",
    "memory_weight",
    "the_lesson",
    "embedding",
    "created_at",
    "last_accessed",
    "access_count"
}


def _load_db_url() -> str:
    """
    Loads the Neon Connection String from the tokens/project_token.json file.
    Expected key: "NEON_DB_URL"
    """
    base_dir = Path(__file__).resolve().parent.parent  # b/
    token_path = base_dir.parent / "tokens" / "project_token.json"

    if not token_path.exists():
        raise RuntimeError(f"CRITICAL ERROR: Token file not found: {token_path}")

    try:
        with token_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            url = data.get("NEON_DB_URL")
            if not url:
                raise ValueError("project_token.json does not contain the 'NEON_DB_URL' key.")
            return url
    except Exception as e:
        raise RuntimeError(f"CRITICAL ERROR loading DB URL: {e}")


def get_db_connection() -> Any:
    """
    Returns an active database connection.
    """
    db_url = _load_db_url()
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True  # Important: CREATE statements must run immediately
        return conn
    except Exception as e:
        raise ConnectionError(f"Failed to connect to the database: {e}")


def _validate_existing_schema(cur: Any) -> bool:
    """
    Checks if the existing table structure matches expectations.
    Raises an error if there is a mismatch.
    """
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s;
    """, (TABLE_NAME,))

    existing_columns = {row[0] for row in cur.fetchall()}

    if not existing_columns:
        return False  # Table does not exist yet

    missing = EXPECTED_COLUMNS - existing_columns
    if missing:
        raise RuntimeError(
            f"DATABASE SCHEMA ERROR! The table '{TABLE_NAME}' exists but columns are missing: {missing}. "
            f"The system will NOT start for safety reasons. Manual intervention required."
        )

    print(f"[DB] Schema validation for '{TABLE_NAME}' successful.")
    return True


def _create_schema(cur: Any) -> None:
    """
    Creates the table and indexes.
    """
    print(f"[DB] Table '{TABLE_NAME}' does not exist. Creating...")

    # 1. Enable vector extension
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create Table
    # dominant_emotions: TEXT[] (Postgres array)
    # embedding: vector(768)
    create_table_sql = f"""
    CREATE TABLE {TABLE_NAME} (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        room_id TEXT NOT NULL,
        model_version TEXT,
        essence TEXT,
        dominant_emotions TEXT[],
        memory_weight FLOAT,
        the_lesson TEXT,
        embedding vector({VECTOR_DIMENSIONS}),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_accessed TIMESTAMPTZ DEFAULT NOW(),
        access_count INT DEFAULT 1
    );
    """
    cur.execute(create_table_sql)

    # 3. Create Indexes
    # Fast filtering by room
    cur.execute(f"CREATE INDEX idx_{TABLE_NAME}_room ON {TABLE_NAME}(room_id);")

    # HNSW index for vector search (cosine similarity: vector_cosine_ops)
    cur.execute(f"""
        CREATE INDEX idx_{TABLE_NAME}_embedding 
        ON {TABLE_NAME} USING hnsw (embedding vector_cosine_ops);
    """)

    print("[DB] Table and indexes created successfully.")


def check_and_initialize_db() -> None:
    """
    Main function to be called at system startup.
    Checks connection and schema.
    """
    print("[DB] Checking database connection...")

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if table exists and is valid
            exists_and_valid = _validate_existing_schema(cur)

            if not exists_and_valid:
                _create_schema(cur)

        conn.close()
        print("[DB] System launch authorized.")

    except Exception as e:
        print(f"\n!!! CRITICAL DATABASE ERROR !!!\n{e}\n")
        sys.exit(1)  # Immediate exit if DB is not healthy


# For testing purposes if run standalone
if __name__ == "__main__":
    check_and_initialize_db()