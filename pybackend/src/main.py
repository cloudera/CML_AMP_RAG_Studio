import os

import boto3
from fastapi.middleware.cors import CORSMiddleware
from src.db.provider import SQLiteConnectionProvider
from src.migration.datastore import SQLiteDatastore
from src.migration.migrator import Migrator
from src.openapi_server.impl.data_source_api import DataSourceApiSingleton
from src.openapi_server.impl.data_source_files_api import (
    DataSourceFilesApiConfig,
    DataSourceFilesApiSingleton,
)
from src.openapi_server.impl.session_api import SessionApiSingleton
from src.openapi_server.main import app
from src.python_migration.python_client import PythonClient
from src.reconcilers.delete_data_source import DeleteDataSourceReconciler
from src.reconcilers.delete_data_source_file import DeleteDataSourceFileReconciler
from src.reconcilers.delete_session import DeleteSessionReconciler
from src.reconcilers.index_data_source_file import IndexDataSourceFileReconciler
from src.reconcilers.summarize_data_source_file import SummarizeDataSourceFileReconciler
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Add this new endpoint after the existing routes
@app.get("/_health")
async def health_check():
    return {"status": "healthy"}


# Initialize the DB
db_connection_provider = SQLiteConnectionProvider(
    os.getenv("SQLITE_DB_PATH", "./db.sqlite")
)
with db_connection_provider.connection() as connection:
    datastore = SQLiteDatastore(connection)
    migrator = Migrator(datastore)
    migrator.perform_migration()

# Initialize the S3 client
s3_client = boto3.client("s3")
s3_bucket_name = os.getenv("S3_RAG_DOCUMENT_BUCKET")
s3_path_prefix = os.getenv("S3_RAG_BUCKET_PREFIX")

# Initialize the Python client
python_client = PythonClient(os.getenv("PYTHON_BASE_URL"))

# Initialize the reconcilers
DeleteDataSourceFileReconciler(
    db_connection_provider=db_connection_provider,
    python_client=python_client,
    s3_bucket_name=s3_bucket_name,
    s3_client=s3_client,
).run()
DeleteDataSourceReconciler(
    db_connection_provider=db_connection_provider,
    python_client=python_client,
).run()
DeleteSessionReconciler(
    db_connection_provider=db_connection_provider,
    python_client=python_client,
).run()
IndexDataSourceFileReconciler(
    db_connection_provider=db_connection_provider,
    python_client=python_client,
    s3_bucket_name=s3_bucket_name,
).run()
SummarizeDataSourceFileReconciler(
    db_connection_provider=db_connection_provider,
    python_client=python_client,
    s3_bucket_name=s3_bucket_name,
).run()

# Initialize the APIs
DataSourceApiSingleton(db_connection_provider=db_connection_provider)
DataSourceFilesApiSingleton(
    db_connection_provider=db_connection_provider,
    config=DataSourceFilesApiConfig(
        bucket_name=s3_bucket_name,
        s3_path_prefix=s3_path_prefix,
    ),
    s3_client=s3_client,
    files_dir=os.getenv("FILES_DIR", "./files"),
)
SessionApiSingleton(db_connection_provider=db_connection_provider)
