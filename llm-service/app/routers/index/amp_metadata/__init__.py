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
from typing import Annotated, Literal, Optional

import fastapi
from fastapi import APIRouter, FastAPI
from subprocess import CompletedProcess

from fastapi.params import Header
from pydantic import BaseModel

from .... import exceptions
from ....services.amp_update import does_amp_need_updating

router = APIRouter(prefix="/amp", tags=["AMP"])

root_dir = (
    "/home/cdsw/rag-studio" if os.getenv("IS_COMPOSABLE", "") != "" else "/home/cdsw"
)


@router.get("", summary="Returns a boolean for whether AMP needs updating.")
@exceptions.propagates
def amp_up_to_date_status(
    remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> bool:
    env = get_project_environment()
    project_owner = env.get("PROJECT_OWNER", "unknown")

    if remote_user == project_owner or remote_user_perm == "RW":
        # noinspection PyBroadException
        try:
            return does_amp_need_updating()
        except Exception:
            return False

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


class AwsConfig(BaseModel):
    """
    Model to represent the AWS configuration.
    """

    region: Optional[str] = None
    document_bucket_name: Optional[str] = None
    bucket_prefix: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None


class AzureConfig(BaseModel):
    """
    Model to represent the Azure configuration.
    """

    openai_key: Optional[str] = None
    openai_endpoint: Optional[str] = None
    openai_api_version: Optional[str] = None


class CaiiConfig(BaseModel):
    """
    Model to represent the CAII configuration.
    """

    caii_domain: Optional[str] = None


class ProjectConfig(BaseModel):
    """
    Model to represent the project configuration.
    """

    use_enhanced_pdf_processing: bool
    aws_config: AwsConfig
    azure_config: AzureConfig
    caii_config: CaiiConfig


DEFAULT_CONFIGURATION = ProjectConfig(
    use_enhanced_pdf_processing=False,
    aws_config=AwsConfig(
        region="us-west-2",
        bucket_prefix="rag-studio",
    ),
    azure_config=AzureConfig(),
    caii_config=CaiiConfig(),
)


@router.get("/config", summary="Returns application configuration.")
@exceptions.propagates
def get_configuration(
    remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> ProjectConfig:
    env = get_project_environment()
    project_owner = env.get("PROJECT_OWNER", "unknown")

    if remote_user == project_owner or remote_user_perm == "RW":
        return env_to_config(env)

    raise fastapi.HTTPException(
        status_code=403,
        detail="You do not have permission to access application configuration.",
    )


def get_project_environment() -> dict[str, str]:
    try:
        import cmlapi

        client = cmlapi.default_client()
        project_id = os.environ["CDSW_PROJECT_ID"]
        project = client.get_project(project_id=project_id)
        return json.loads(project.environment)
    except ImportError:
        return dict(os.environ)


def env_to_config(env: dict[str, str]) -> ProjectConfig:
    """
    Converts environment variables to a ProjectConfig object.
    """
    aws_config = AwsConfig(
        region=env.get("AWS_DEFAULT_REGION"),
        document_bucket_name=env.get("S3_RAG_DOCUMENT_BUCKET"),
        bucket_prefix=env.get("S3_RAG_BUCKET_PREFIX"),
        access_key_id=env.get("AWS_ACCESS_KEY_ID"),
        secret_access_key=env.get("AWS_SECRET_ACCESS_KEY"),
    )
    azure_config = AzureConfig(
        openai_key=env.get("AZURE_OPENAI_API_KEY"),
        openai_endpoint=env.get("AZURE_OPENAI_ENDPOINT"),
        openai_api_version=env.get("OPENAI_API_VERSION"),
    )
    caii_config = CaiiConfig(
        caii_domain=env.get("CAII_DOMAIN"),
    )
    return ProjectConfig(
        use_enhanced_pdf_processing=env.get("USE_ENHANCED_PDF_PROCESSING", False),
        aws_config=aws_config,
        azure_config=azure_config,
        caii_config=caii_config,
    )
