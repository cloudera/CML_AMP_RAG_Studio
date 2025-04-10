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
import os
import socket
import subprocess
from subprocess import CompletedProcess
from typing import Annotated, Optional, cast

import fastapi
from fastapi import APIRouter
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
    is_valid_config: bool


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


@router.post("/config", summary="Updates application configuration.")
@exceptions.propagates
def update_configuration(
    config: ProjectConfig,
    remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> ProjectConfig:
    existing_env = get_project_environment()
    project_owner = existing_env.get("PROJECT_OWNER", "unknown")

    if remote_user == project_owner or remote_user_perm == "RW":
        # merge the new configuration with the existing one
        updated_env = config_to_env(config)
        env_to_save = existing_env | updated_env
        update_project_environment(env_to_save)

        return env_to_config(get_project_environment())

    raise fastapi.HTTPException(
        status_code=403,
        detail="You do not have permission to access application configuration.",
    )


@router.post("/restart-application", summary="Restarts the application.")
@exceptions.propagates
def restart_application() -> str:
    print(
        subprocess.run(
            [f"python {root_dir}/scripts/refresh_project.py"],
            shell=True,
            check=True,
        )
    )
    return "OK"


def update_project_environment(new_env: dict[str, str]) -> None:
    try:
        import cmlapi

        client = cmlapi.default_client()
        project_id = os.environ["CDSW_PROJECT_ID"]
        project = client.get_project(project_id=project_id)
        project.environment = json.dumps(new_env)
        client.update_project(project_id=project_id, body=project)
    except ImportError:
        pass


def get_project_environment() -> dict[str, str]:
    try:
        import cmlapi

        client = cmlapi.default_client()
        project_id = os.environ["CDSW_PROJECT_ID"]
        project = client.get_project(project_id=project_id)
        return cast(dict[str, str], json.loads(project.environment))
    except ImportError:
        return dict(os.environ)


def config_to_env(config: ProjectConfig) -> dict[str, str]:
    """
    Converts a ProjectConfig object to a dictionary of environment variables.
    """
    return {
        "USE_ENHANCED_PDF_PROCESSING": str(config.use_enhanced_pdf_processing).lower(),
        "AWS_DEFAULT_REGION": config.aws_config.region or "",
        "S3_RAG_DOCUMENT_BUCKET": config.aws_config.document_bucket_name or "",
        "S3_RAG_BUCKET_PREFIX": config.aws_config.bucket_prefix or "",
        "AWS_ACCESS_KEY_ID": config.aws_config.access_key_id or "",
        "AWS_SECRET_ACCESS_KEY": config.aws_config.secret_access_key or "",
        "AZURE_OPENAI_API_KEY": config.azure_config.openai_key or "",
        "AZURE_OPENAI_ENDPOINT": config.azure_config.openai_endpoint or "",
        "OPENAI_API_VERSION": config.azure_config.openai_api_version or "",
        "CAII_DOMAIN": config.caii_config.caii_domain or "",
    }


def validate(environ: dict[str, str]):
    print("Validating environment variables...")
    #  aws
    access_key_id = environ.get("AWS_ACCESS_KEY_ID") or None
    secret_key_id = environ.get("AWS_SECRET_ACCESS_KEY") or None
    default_region = environ.get("AWS_DEFAULT_REGION") or None
    document_bucket = environ.get("S3_RAG_DOCUMENT_BUCKET") or None

    # azure
    azure_openai_api_key = environ.get("AZURE_OPENAI_API_KEY") or None
    azure_openai_endpoint = environ.get("AZURE_OPENAI_ENDPOINT") or None
    openai_api_version = environ.get("OPENAI_API_VERSION") or None

    # caii
    caii_domain = environ.get("CAII_DOMAIN") or None

    # 1. if you don't have a caii_domain, you _must_ have an access key, secret key, and default region
    if caii_domain is not None:
        print("Using CAII for LLMs/embeddings; CAII_DOMAIN is set")
        try:
            socket.gethostbyname(caii_domain)
            print(f"CAII domain {caii_domain} can be resolved")
        except socket.error:
            print(f"ERROR: CAII domain {caii_domain} can not be resolved")
            return False
    elif any([access_key_id, secret_key_id, default_region]):
        if all([access_key_id, secret_key_id, default_region]):
            print(
                "Using Bedrock for LLMs/embeddings; AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION are set"
            )

        # 2. if you have a document_bucket, you _must_ have an access key, secret key, and default region
        if document_bucket is not None:
            if access_key_id is None or secret_key_id is None or default_region is None:
                print(
                    "ERROR: Using S3 for document storage; missing required environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION"
                )
                return False

        if document_bucket is not None:
            print("Using S3 for document storage (S3_RAG_DOCUMENT_BUCKET is set)")
        else:
            print(
                "Using the project filesystem for document storage (S3_RAG_DOCUMENT_BUCKET is not set)"
            )
            # TODO: verify that the bucket prefix is always optional
    elif all([azure_openai_api_key, azure_openai_endpoint, openai_api_version]):
        print(
            "Using Azure for LLMs/embeddings; AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and OPENAI_API_VERSION are set"
        )
    else:
        print("ERROR: Missing required environment variables for modeling serving")
        print(
            "ERROR: If using Bedrock for LLMs/embeddings; missing required environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION"
        )
        print(
            "ERROR: If using Azure for LLMs/embeddings; missing required environment variables: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, OPENAI_API_VERSION"
        )
        print(
            "ERROR: If using CAII for LLMs/embeddings; missing required environment variables: CAII_DOMAIN"
        )
        return False
    return True


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
        use_enhanced_pdf_processing=cast(
            bool, env.get("USE_ENHANCED_PDF_PROCESSING", False)
        ),
        aws_config=aws_config,
        azure_config=azure_config,
        caii_config=caii_config,
        is_valid_config=validate(env),
    )
