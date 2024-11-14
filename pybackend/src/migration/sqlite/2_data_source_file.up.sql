CREATE TABLE data_source_files (
    id VARCHAR(255) PRIMARY KEY,
    blob BLOB NOT NULL,
    data_source_id UNSIGNED BIG INT NOT NULL,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);
