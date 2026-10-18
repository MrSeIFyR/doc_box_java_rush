CREATE TABLE IF NOT EXISTS documents (
    id              SERIAL PRIMARY KEY,
    stored_name     varchar(128) NOT NULL UNIQUE,
    original_name   varchar(128) NOT NULL,
    size_bytes      INTEGER NOT NULL,
    upload_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extension       varchar(128) NOT NULL
);