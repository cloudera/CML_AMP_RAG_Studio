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
import json
import subprocess
import os
from typing import Annotated

import fastapi
from fastapi import APIRouter, FastAPI
from subprocess import CompletedProcess

from fastapi.params import Header

from .... import exceptions
from ....services.amp_update import does_amp_need_updating

router = APIRouter(prefix="/amp-update", tags=["AMP Update"])

root_dir = (
    "/home/cdsw/rag-studio" if os.getenv("IS_COMPOSABLE", "") != "" else "/home/cdsw"
)


@router.get("", summary="Returns a boolean for whether AMP needs updating.")
@exceptions.propagates
def amp_up_to_date_status() -> bool:
    # noinspection PyBroadException
    try:
        return does_amp_need_updating()
    except Exception:
        return False


@router.post("", summary="Updates AMP.")
@exceptions.propagates
def update_amp() -> str:
    print(
        subprocess.run(
            [f"python {root_dir}/llm-service/scripts/run_refresh_job.py"],
            shell=True,
            check=True,
        )
    )
    return "OK"


@router.get("/job-status", summary="Get AMP Status.")
@exceptions.propagates
def get_amp_status() -> str:
    process: CompletedProcess[bytes] = subprocess.run(
        [f"python {root_dir}/llm-service/scripts/get_job_run_status.py"],
        shell=True,
        check=True,
        capture_output=True,
    )
    stdout = process.stdout.decode("utf-8")
    return stdout.strip()


@router.get(
    "/is-composable", summary="Returns a boolean for whether AMP is composable."
)
@exceptions.propagates
def amp_is_composed() -> bool:
    return os.getenv("IS_COMPOSABLE", "") != "" or False


@router.get("/cml-env-vars", summary="Returns the environment variables.")
@exceptions.propagates
def get_cml_env_vars(
    remote_user: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    try:
        import cmlapi

    except ImportError:
        return {
            "AWS_DEFAULT_REGION": "us-west-2",
            "S3_RAG_DOCUMENT_BUCKET": "",
            "S3_RAG_BUCKET_PREFIX": "rag-studio",
            "AWS_ACCESS_KEY_ID": "",
            "AWS_SECRET_ACCESS_KEY": "",
            "USE_ENHANCED_PDF_PROCESSING": "false",
            "CAII_DOMAIN": "",
            "CDP_TOKEN_OVERRIDE": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_ENDPOINT": "",
            "OPENAI_API_VERSION": "",
            "PROJECT_OWNER": "",
        }

    client = cmlapi.default_client()
    project_id = os.environ["CDSW_PROJECT_ID"]
    project = client.get_project(project_id=project_id)
    env = json.loads(project.environment)
    project_owner = env["PROJECT_OWNER"]
    if remote_user != project_owner:
        raise fastapi.HTTPException(
            status_code=403,
            detail="You do not have permission to access these environment variables.",
        )
