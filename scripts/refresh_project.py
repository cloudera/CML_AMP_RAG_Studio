# ##############################################################################
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
# ##############################################################################

import os
import subprocess
import cmlapi

root_dir = (
    "/home/cdsw/rag-studio" if os.getenv("IS_COMPOSABLE", "") != "" else "/home/cdsw"
)
os.chdir(root_dir)

print(subprocess.run(["git", "stash"], check=True))
print(subprocess.run(["git", "pull", "--rebase"], check=True))
print(subprocess.run(["bash", "scripts/refresh_project.sh"], check=True))


client = cmlapi.default_client()
project_id = os.environ["CDSW_PROJECT_ID"]
apps = client.list_applications(project_id=project_id)
if len(apps.applications) > 0:
    # find the application named "RagStudio" and restart it
    ragstudio_qdrant = next(
        (app for app in apps.applications if app.name == "RagStudioQdrant"), None
    )
    if ragstudio_qdrant:
        if ragstudio_qdrant.status != "APPLICATION_RUNNING":
            app_id = ragstudio_qdrant.id
            print("Restarting app with ID: ", app_id)
            client.restart_application(application_id=app_id, project_id=project_id)
    else:
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
            },
        )
        client.restart_application(application_id=application.id, project_id=project_id)

print(
    "Project refresh complete. Restarting the RagStudio Application to pick up changes, if this isn't the initial deployment."
)

print(subprocess.run("python scripts/restart_app.py", shell=True, check=True))
