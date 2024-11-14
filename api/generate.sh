#!/bin/bash

set -eo pipefail

# Merge the base API spec
cat defs/api_base.yaml > api.yaml

# Add the paths section
echo 'paths:' >> api.yaml
for file in defs/paths/*.yaml; do
    echo "Adding $file to api.yaml"
    cat "$file" | sed 's/^/  /' >> api.yaml
    echo '' >> api.yaml
done


# Add each component file to the API spec, with the proper indentation
echo 'components:' >> api.yaml
echo '  schemas:' >> api.yaml
for file in defs/components/schemas/*.yaml; do
    echo "Adding $file to api.yaml"
    cat "$file" | sed 's/^/    /' >> api.yaml
    echo '' >> api.yaml
done

echo "Generating API client"
openapi-generator-cli generate -i api.yaml -g typescript-axios -o typescript-client
rm openapitools.json
mkdir -p ../ui/src/services/api/
mv typescript-client/api.ts ../ui/src/services/api/api.ts
mv typescript-client/base.ts ../ui/src/services/api/base.ts
mv typescript-client/common.ts ../ui/src/services/api/common.ts
mv typescript-client/configuration.ts ../ui/src/services/api/configuration.ts
for f in ../ui/src/services/api/*.ts; do
    echo "Fixing $f"
    # Remove the first line
    sed -i'.bak' '1d' "$f"
    rm "${f}.bak"
done
rm -rf typescript-client

echo "Generating FastAPI server"
openapi-generator-cli generate -i api.yaml -g python-fastapi -o fastapi-server
# For each file in the apis, fix the "file" representation
for f in fastapi-server/src/openapi_server/apis/*.py; do
    echo "Fixing $f"
    # Import FileResponse above "from fastapi import"
    sed -i'.bak' 's/from fastapi import/from fastapi.responses import FileResponse\nfrom fastapi import/g' "$f"
    rm "${f}.bak"
    # Import File and UploadFile above "from fastapi import"
    sed -i'.bak' 's/from fastapi import/from fastapi import File, UploadFile\nfrom fastapi import/g' "$f"
    rm "${f}.bak"
    # Import FilwResponse below "from typing import ClassVar, Dict, List, Tuple"
    sed -i'.bak' 's/from typing import ClassVar, Dict, List, Tuple/from typing import ClassVar, Dict, List, Tuple\nfrom fastapi.responses import FileResponse/g' "$f"
    rm "${f}.bak"
    # Import File and UploadFile below "from typing import ClassVar, Dict, List, Tuple"
    sed -i'.bak' 's/from typing import ClassVar, Dict, List, Tuple/from typing import ClassVar, Dict, List, Tuple\nfrom fastapi import File, UploadFile/g' "$f"
    rm "${f}.bak"
    # Replace returns like "-> file" with "-> FileResponse"
    sed -i'.bak' 's/-> file/-> FileResponse/g' "$f"
    rm "${f}.bak"
    # Replace models like '"model": file' with '"model": FileResponse'
    sed -i'.bak' 's/"model": file/"model": FileResponse/g' "$f"
    rm "${f}.bak"
    # Replace "file: str = Form(None, " with "file: UploadFile = File(..."
    sed -i'.bak' 's/file: str = Form(None,/file: UploadFile = File(...,/g' "$f"
    rm "${f}.bak"
    # Replace "file: str" with "file: UploadFile"
    sed -i'.bak' 's/file: str/file: UploadFile/g' "$f"
    rm "${f}.bak"
    # Use sed to search for responses containing "model": FileResponse and replace it with response_class since FileResponse is not a valid type in FastAPI
    sed -i'.bak' '/responses={/{N;N;s/    responses={\n        200: {"model": FileResponse,.*\n    },/    response_class=FileResponse,/;}' "$f"
    rm "${f}.bak"
    # Add prefix to the routes
    sed -i'.bak' 's,router = APIRouter(),router = APIRouter(prefix="/api/v1"),g' "$f"
    rm "${f}.bak"
    # Remove async/await from the routes
    sed -i'.bak' 's/async //g' "$f"
    rm "${f}.bak"
    sed -i'.bak' 's/await //g' "$f"
    rm "${f}.bak"
done
for f in fastapi-server/src/openapi_server/models/*.py; do
    echo "Fixing $f"
    # Replace "import object" with "import ObjectModel"
    sed -i'.bak' 's/import object/import ObjectModel/g' "$f"
    rm "${f}.bak"
    # Replace "class ...(object)" with "class ...(ObjectModel)"
    sed -i'.bak' 's/class \([^ ]*\)(object)/class \1(ObjectModel)/g' "$f"
    rm "${f}.bak"
done
for f in $(find fastapi-server/src/openapi_server/ -name '*.py'); do
    echo "Fixing $f"
    # Add src to the imports
    sed -i'.bak' 's/^import openapi_server/import src.openapi_server/g' "$f"
    rm "${f}.bak"
    sed -i'.bak' 's/^from openapi_server/from src.openapi_server/g' "$f"
    rm "${f}.bak"
    sed -i'.bak' 's/^ns_pkg = openapi_server.impl$/ns_pkg = src.openapi_server.impl/g' "$f"
    rm "${f}.bak"
done

rm openapitools.json
mkdir -p ../pybackend/src/openapi_server/
rm -rf fastapi-server/src/openapi_server/impl
rm -rf ../pybackend/src/openapi_server/apis
rm -rf ../pybackend/src/openapi_server/models
mv fastapi-server/src/openapi_server/* ../pybackend/src/openapi_server/
rm -rf fastapi-server
git checkout -- ../pybackend/src/openapi_server/models/object.py

