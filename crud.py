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

def add_file(stored_name, original_name, size_bytes, extension):
    cursor = connection.cursor()
    cursor.execute("""
                INSERT INTO documents (stored_name, original_name, size_bytes, extension)
                VALUES (%s, %s, %s, %s)
                """, (stored_name, original_name, size_bytes, extension))
    connection.commit()

def get_by_id(id):
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                SELECT 
                    stored_name
                FROM documents
    """)
    return cursor.fetchone()

def remove_file(id):
    cursor = connection.cursor()
    cursor.execute("""
                DELETE FROM documents 
                WHERE id = %s
    """, (id,))
    connection.commit()

def get_by_query(name: str=""):
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"""
                SELECT 
                    id, 
                    stored_name, 
                    original_name,
                    extension,
                    upload_at,
                    round(size_bytes / 1024, 1)  as size_kb 
                FROM documents
                WHERE original_name LIKE '%{name}%'
                ORDER BY upload_at DESC
                """)
    return cursor.fetchall()