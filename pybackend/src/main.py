import os
import sys
from importlib import import_module

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

# Update sys path so that src can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.provider import SQLiteConnectionProviderSingleton
from src.java_migration.client import JavaClient
from src.java_migration.migrate import JavaMigrator
from src.openapi_server.main import app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


def import_recursively(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                module_path = os.path.join(root, file)
                module_name = os.path.relpath(module_path, directory).replace(
                    os.path.sep, "."
                )[:-3]
                import_module(f"{module_name}")


# Import every py file in this folder and its subfolders recursively
import_recursively(os.path.dirname(__file__))


# Add this new endpoint after the existing routes
@app.get("/_health")
async def health_check():
    return {"status": "healthy"}


SQLiteConnectionProviderSingleton()


JavaMigrator(
    JavaClient(
        os.getenv("JAVA_BASE_URL"),
    ),
    SQLiteConnectionProviderSingleton(),
).migrate()
