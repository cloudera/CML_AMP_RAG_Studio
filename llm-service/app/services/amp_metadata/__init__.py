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
import json
import os
import socket
from typing import Optional, cast, Literal

from pydantic import BaseModel

SummaryStorageProviderType = Literal["Local", "S3"]


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
    summary_storage_provider: SummaryStorageProviderType
    aws_config: AwsConfig
    azure_config: AzureConfig
    caii_config: CaiiConfig
    release_version: str


class ProjectConfigWithValidation(ProjectConfig):
    """
    Model to represent the project configuration.
    """

    is_valid_config: bool


def validate_storage_config(environ: dict[str, str]) -> bool:
    access_key_id = environ.get("AWS_ACCESS_KEY_ID") or None
    secret_key_id = environ.get("AWS_SECRET_ACCESS_KEY") or None
    default_region = environ.get("AWS_DEFAULT_REGION") or None
    document_bucket = environ.get("S3_RAG_DOCUMENT_BUCKET") or None

    if document_bucket is not None:
        if access_key_id is None or secret_key_id is None or default_region is None:
            print(
                "ERROR: Using S3 for document storage; missing required environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION"
            )
            return False
    return True


def validate_model_config(environ: dict[str, str]) -> bool:
    #  aws
    access_key_id = environ.get("AWS_ACCESS_KEY_ID") or None
    secret_key_id = environ.get("AWS_SECRET_ACCESS_KEY") or None
    default_region = environ.get("AWS_DEFAULT_REGION") or None

    # azure
    azure_openai_api_key = environ.get("AZURE_OPENAI_API_KEY") or None
    azure_openai_endpoint = environ.get("AZURE_OPENAI_ENDPOINT") or None
    openai_api_version = environ.get("OPENAI_API_VERSION") or None

    # caii
    caii_domain = environ.get("CAII_DOMAIN") or None

    valid_model_config_exists = False
    # 1. if you don't have a caii_domain, you _must_ have an access key, secret key, and default region
    if caii_domain is not None:
        print("Using CAII for LLMs/embeddings; CAII_DOMAIN is set")
        try:
            socket.gethostbyname(caii_domain)
            print(f"CAII domain {caii_domain} can be resolved")
            valid_model_config_exists = True
        except socket.error:
            print(f"ERROR: CAII domain {caii_domain} can not be resolved")

    if any([access_key_id, secret_key_id, default_region]):
        if all([access_key_id, secret_key_id, default_region]):
            valid_model_config_exists = True
        else:
            print(
                "AWS Config does not contain all required keys; AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION are not all set"
            )

    if any([azure_openai_api_key, azure_openai_endpoint, openai_api_version]):
        if all([azure_openai_api_key, azure_openai_endpoint, openai_api_version]):
            valid_model_config_exists = True
        else:
            print(
                "Azure config is not valid for LLMs/embeddings; AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and OPENAI_API_VERSION are all needed."
            )

    return valid_model_config_exists


def validate(environ: dict[str, str]) -> bool:
    print("Validating environment variables...")
    storage_options_valid = validate_storage_config(environ)
    valid_model_options = validate_model_config(environ)

    if not valid_model_options or not storage_options_valid:
        print("ERROR: Invalid configuration options")
        return False
    return True


def config_to_env(config: ProjectConfig) -> dict[str, str]:
    """
    Converts a ProjectConfig object to a dictionary of environment variables.
    """
    return {
        "USE_ENHANCED_PDF_PROCESSING": str(config.use_enhanced_pdf_processing).lower(),
        "SUMMARY_STORAGE_PROVIDER": config.summary_storage_provider or "Local",
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


def env_to_config(env: dict[str, str]) -> ProjectConfigWithValidation:
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
    return ProjectConfigWithValidation(
        use_enhanced_pdf_processing=cast(
            bool,
            env.get("USE_ENHANCED_PDF_PROCESSING", False),
        ),
        summary_storage_provider=cast(
            SummaryStorageProviderType,
            env.get("SUMMARY_STORAGE_PROVIDER", "Local"),
        ),
        aws_config=aws_config,
        azure_config=azure_config,
        caii_config=caii_config,
        is_valid_config=validate(env),
        release_version=env.get("RELEASE_TAG", "unknown"),
    )


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
