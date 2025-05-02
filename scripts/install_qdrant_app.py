import os
import time

import cmlapi

client = cmlapi.default_client()
project_id = os.environ["CDSW_PROJECT_ID"]
apps = client.list_applications(project_id=project_id)
if len(apps.applications) > 0:
    ragstudio_app = next(
        (app for app in apps.applications if app.name == "RagStudio"), None
    )
    if ragstudio_app:
        runtime_image = ragstudio_app.runtime_identifier
    else:
        raise ValueError(
            "RagStudio application not found. Please install the RagStudio application first."
        )

    # find the application named "RagStudioQdrant" and restart it
    ragstudio_qdrant = next(
        (app for app in apps.applications if app.name == "RagStudioQdrant"), None
    )
    if ragstudio_qdrant:
        # if ragstudio_qdrant.status != "APPLICATION_RUNNING":
        app_id = ragstudio_qdrant.id
    else:
        client.stop_application(
            project_id=project_id,
            application_id=ragstudio_app.id,
        )
        application = client.create_application(
            project_id=project_id,
            body={
                "name": "RagStudioQdrant",
                "subdomain": "ragstudioqdrant",
                "bypass_authentication": False,
                "static_subdomain": False,
                "script": "scripts/startup_qdrant.py",
                "short_summary": "Create and start RagStudio's Qdrant instance.",
                "long_summary": "Create and start RagStudio Qdrant instance.",
                "cpu": 2,
                "memory": 4,
                "environment_variables": {
                    "TASK_TYPE": "START_APPLICATION",
                },
                "kernel": "python3",
                "runtime_identifier": runtime_image,
            },
        )
        app_id = application.id
    print("Restarting app with ID: ", app_id)
    client.restart_application(application_id=app_id, project_id=project_id)

    while True:
        qdrant_app = client.get_application(
            project_id=project_id, application_id=app_id
        )
        if qdrant_app.status == "APPLICATION_RUNNING":
            break
        print("Waiting for RagStudio Qdrant to start...")
        time.sleep(5)
