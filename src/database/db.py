import psycopg2
from psycopg2.extras import RealDictCursor
from src.config.settings import settings, logger

def get_connection():
    """Establish a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=5432,
    )

def init_db():
    """Create the sessions and messages tables if they do not exist."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Sessions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Messages table
                # Note: Modified to handle pre-existing TEXT session_id columns smoothly
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            conn.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def create_session(title: str = "New Chat") -> int:
    """Create a new chat session and return its ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sessions (title) VALUES (%s) RETURNING id;", 
                (title,)
            )
            session_id = cur.fetchone()[0]
        conn.commit()
        return session_id

def get_all_sessions():
    """Retrieve all chat sessions, ordered by newest first."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC;")
            return cur.fetchall()

def get_messages_for_session(session_id):
    """Retrieve all messages for a specific session."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # We explicitly cast both sides to text to prevent type mismatches 
            # with any pre-existing tables in your database.
            cur.execute(
                "SELECT role, content FROM messages WHERE session_id::text = %s::text ORDER BY created_at ASC;",
                (str(session_id),)
            )
            return cur.fetchall()

def add_message(session_id, role: str, content: str):
    """Insert a new message into the database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Pass the session_id as a string so it plays nice with older TEXT columns
            cur.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s);",
                (str(session_id), role, content)
            )
        conn.commit()

def update_session_title(session_id, title: str):
    """Update the title of a session (e.g., based on the first prompt)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Cast session_id to integer for the sessions table which uses SERIAL
            cur.execute("UPDATE sessions SET title = %s WHERE id = %s::int;", (title, int(session_id)))
        conn.commit()