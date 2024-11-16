import os
import sys

import uvicorn

# Update sys path so that src can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    uvicorn.run(
        "app_main:app", host="0.0.0.0", port=8080, reload=True, log_level="debug"
    )
