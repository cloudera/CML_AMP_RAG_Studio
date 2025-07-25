#
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
#  Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
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
#

import os
import time

import cmlapi

time.sleep(0.1)
client = cmlapi.default_client()
project_id = os.environ["CDSW_PROJECT_ID"]
cml_apps = client.list_applications(project_id=project_id)
# ragstudio_apps = ["RagStudioMetadata", "RagStudio"]
ragstudio_apps = ["RagStudio"]

if len(cml_apps.applications) > 0:
    for app_name in ragstudio_apps:
        cml_ragstudio_app = next(
            (cml_app for cml_app in cml_apps.applications if cml_app.name.startswith(app_name)),
            None,
        )

        if cml_ragstudio_app:
            app_id = cml_ragstudio_app.id
            print("Restarting app with ID: ", app_id)
            client.restart_application(application_id=app_id, project_id=project_id)
        else:
            print(
                "No RagStudio application found to restart. This can happen if someone renamed the application."
            )
            # if we're in "studio" mode, then there might be other applications that are not named RagStudio (Agent Studio, etc.)
            if os.getenv("IS_COMPOSABLE", "") != "":
                print("Composable environment. This is likely the initial deployment.")
            else:
                raise ValueError("RagStudio application not found to restart")
else:
    print("No applications found to restart. This is likely the initial deployment.")
