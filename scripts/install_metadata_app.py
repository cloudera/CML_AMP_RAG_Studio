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
    # find the application named "RagStudioMetadata" and restart it
    ragstudio_metadata = next(
        (app for app in apps.applications if app.name == "RagStudioMetadata"), None
    )
    if ragstudio_metadata:
        app_id = ragstudio_metadata.id
    else:
        client.stop_application(
            project_id=project_id,
            application_id=ragstudio_app.id,
        )

        application = client.create_application(
            project_id=project_id,
            body={
                "name": "RagStudioMetadata",
                "subdomain": "ragstudiometadata",
                "bypass_authentication": False,
                "static_subdomain": False,
                "script": "scripts/startup_metadata_app.py",
                "short_summary": "Create and start RagStudio's Metadata API instance.",
                "long_summary": "Create and start RagStudio Metadata API instance.",
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
        metadata_app = client.get_application(
            project_id=project_id, application_id=app_id
        )
        if metadata_app.status == "APPLICATION_RUNNING":
            break
        print("Waiting for RagStudio Metadata API to start...")
        time.sleep(5)
