import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

connection = psycopg2.connect(**DB_CONFIG)

def get_files_count():
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    return cursor.fetchone()[0]

def get_count_by_query(name: str = ""):
    if not name:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        return cursor.fetchone()[0]

    pattern = f"%{name}%"
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM documents
        WHERE original_name ILIKE %s OR stored_name ILIKE %s
        """,
        (pattern, pattern)
    )
    return cursor.fetchone()[0]

def add_file(stored_name, original_name, size_bytes, extension):
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO documents (stored_name, original_name, size_bytes, extension)
        VALUES (%s, %s, %s, %s)
    """, (stored_name, original_name, size_bytes, extension))
    connection.commit()

def get_by_id(doc_id):
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM documents WHERE id = %s",
        (doc_id,)
    )
    return cursor.fetchone()

def remove_file(doc_id):
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM documents WHERE id = %s",
        (doc_id,)
    )
    connection.commit()

def get_by_query(name: str = "", page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page

    cursor = connection.cursor(cursor_factory=RealDictCursor)

    if not name:
        query = """
            SELECT 
                id, 
                stored_name, 
                original_name,
                extension,
                upload_at,
                round(size_bytes / 1024, 1) AS size_kb 
            FROM documents
            ORDER BY upload_at DESC, id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (per_page, offset))
    else:
        pattern = f"%{name}%"
        query = """
            SELECT 
                id, 
                stored_name, 
                original_name,
                extension,
                upload_at,
                round(size_bytes / 1024, 1) AS size_kb 
            FROM documents
            WHERE original_name ILIKE %s OR stored_name ILIKE %s
            ORDER BY upload_at DESC, id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (pattern, pattern, per_page, offset))

    return cursor.fetchall()
