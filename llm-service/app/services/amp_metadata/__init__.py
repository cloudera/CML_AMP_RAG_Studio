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
import subprocess
from typing import Optional, cast, Protocol

from pydantic import BaseModel, TypeAdapter

from app.config import (
    settings,
    SummaryStorageProviderType,
    ChatStoreProviderType,
    VectorDbProviderType,
    MetadataDbProviderType,
)


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


class OpenAiConfig(BaseModel):
    """
    Model to represent the OpenAI configuration.
    """

    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None


class OpenSearchConfig(BaseModel):

    opensearch_username: Optional[str] = None
    opensearch_password: Optional[str] = None
    opensearch_endpoint: Optional[str] = None
    opensearch_namespace: Optional[str] = None


class MetadataDbConfig(BaseModel):
    jdbc_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ValidationResult(BaseModel):
    valid: bool
    message: str


class ConfigValidationResults(BaseModel):
    storage: ValidationResult
    model: ValidationResult
    metadata_api: ValidationResult
    valid: bool


class ProjectConfig(BaseModel):
    """
    Model to represent the project configuration.
    """

    use_enhanced_pdf_processing: Optional[bool] = False
    summary_storage_provider: SummaryStorageProviderType
    chat_store_provider: ChatStoreProviderType
    vector_db_provider: VectorDbProviderType
    metadata_db_provider: MetadataDbProviderType
    aws_config: AwsConfig
    azure_config: AzureConfig
    caii_config: CaiiConfig
    openai_config: OpenAiConfig
    opensearch_config: OpenSearchConfig
    metadata_db_config: MetadataDbConfig
    cdp_token: Optional[str] = None


class ApplicationConfig(BaseModel):
    """
    Model to represent the application configuration.
    """

    num_of_gpus: int
    memory_size_gb: float


class ProjectConfigPlus(ProjectConfig):
    """
    Model to represent the project configuration.
    """

    release_version: Optional[str] = None
    is_valid_config: bool
    config_validation_results: ConfigValidationResults
    application_config: ApplicationConfig


def validate_storage_config(environ: dict[str, str]) -> ValidationResult:
    access_key_id = environ.get("AWS_ACCESS_KEY_ID") or None
    secret_key_id = environ.get("AWS_SECRET_ACCESS_KEY") or None
    default_region = environ.get("AWS_DEFAULT_REGION") or None
    document_bucket = environ.get("S3_RAG_DOCUMENT_BUCKET") or None

    if document_bucket is not None:
        if access_key_id is None or secret_key_id is None or default_region is None:
            print(
                "ERROR: Using S3 for document storage; missing required environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION"
            )
            return ValidationResult(
                valid=False,
                message="Using S3 for document storage; missing required configuration: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION",
            )
    return ValidationResult(valid=True, message="Storage configuration is valid.")


def validate_model_config(environ: dict[str, str]) -> ValidationResult:
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

    open_ai_key = environ.get("OPENAI_API_KEY") or None

    message = ""
    valid_model_config_exists = False
    # 1. if you don't have a caii_domain, you _must_ have an access key, secret key, and default region
    if caii_domain is not None:
        print("Using CAII for LLMs/embeddings; CAII_DOMAIN is set")
        try:
            socket.gethostbyname(caii_domain)
            print(f"CAII domain {caii_domain} can be resolved")
            valid_model_config_exists = True
            message = "CAII domain is set and can be resolved. \n"
        except socket.error:
            print(f"ERROR: CAII domain {caii_domain} can not be resolved")
            message = message + f"CAII domain {caii_domain} can not be resolved. \n"

    if any([access_key_id, secret_key_id, default_region]):
        if all([access_key_id, secret_key_id, default_region]):
            valid_model_config_exists = True
            message = "AWS Config is valid for Bedrock. \n"
        else:
            print(
                "AWS Config does not contain all required keys; AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION are not all set"
            )
            message = (
                message
                + "AWS Config does not contain all required keys; AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION are not all set. \n"
            )

    if any([azure_openai_api_key, azure_openai_endpoint, openai_api_version]):
        if all([azure_openai_api_key, azure_openai_endpoint, openai_api_version]):
            valid_model_config_exists = True
            message = "Azure config is valid. \n"
        else:
            print(
                "Azure config is not valid; AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and OPENAI_API_VERSION are all needed."
            )
            message = message + (
                "Azure config is not valid; AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and OPENAI_API_VERSION are all needed. \n"
            )

    if any([open_ai_key]):
        if open_ai_key:
            valid_model_config_exists = True
            message = "OpenAI config is valid. \n"
    return ValidationResult(valid=valid_model_config_exists, message=message)


def validate(environ: dict[str, str]) -> ConfigValidationResults:
    print("Validating environment variables...")
    storage_config = validate_storage_config(environ)
    model_config = validate_model_config(environ)

    jdbc_config = validate_jdbc(
        TypeAdapter(MetadataDbProviderType).validate_python(
            environ.get("DB_TYPE", "H2")
        ),
        environ.get("DB_URL", "jdbc:h2:../databases/rag"),
        environ.get("DB_PASSWORD", ""),
        environ.get("DB_USERNAME", ""),
    )

    overall_valid = model_config.valid and storage_config.valid and jdbc_config.valid
    return ConfigValidationResults(
        storage=storage_config,
        model=model_config,
        metadata_api=jdbc_config,
        valid=overall_valid,
    )


def config_to_env(config: ProjectConfig) -> dict[str, str]:
    """
    Converts a ProjectConfig object to a dictionary of environment variables.
    """
    new_env = {
        key: str(value)
        for key, value in {
            "USE_ENHANCED_PDF_PROCESSING": str(
                config.use_enhanced_pdf_processing
            ).lower(),
            "SUMMARY_STORAGE_PROVIDER": config.summary_storage_provider or "Local",
            "CHAT_STORE_PROVIDER": config.chat_store_provider or "Local",
            "VECTOR_DB_PROVIDER": config.vector_db_provider or "QDRANT",
            "AWS_DEFAULT_REGION": config.aws_config.region or "",
            "S3_RAG_DOCUMENT_BUCKET": config.aws_config.document_bucket_name or "",
            "S3_RAG_BUCKET_PREFIX": config.aws_config.bucket_prefix or "",
            "AWS_ACCESS_KEY_ID": config.aws_config.access_key_id or "",
            "AWS_SECRET_ACCESS_KEY": config.aws_config.secret_access_key or "",
            "AZURE_OPENAI_API_KEY": config.azure_config.openai_key or "",
            "AZURE_OPENAI_ENDPOINT": config.azure_config.openai_endpoint or "",
            "OPENAI_API_VERSION": config.azure_config.openai_api_version or "",
            "CAII_DOMAIN": config.caii_config.caii_domain or "",
            "OPENSEARCH_USERNAME": config.opensearch_config.opensearch_username or "",
            "OPENSEARCH_PASSWORD": config.opensearch_config.opensearch_password or "",
            "OPENSEARCH_ENDPOINT": config.opensearch_config.opensearch_endpoint or "",
            "OPENSEARCH_NAMESPACE": config.opensearch_config.opensearch_namespace or "",
            "OPENAI_API_KEY": config.openai_config.openai_api_key or "",
            "OPENAI_API_BASE": config.openai_config.openai_api_base or "",
            "DB_TYPE": config.metadata_db_provider or "H2",
            "DB_URL": (config.metadata_db_config.jdbc_url),
            "DB_USERNAME": (config.metadata_db_config.username),
            "DB_PASSWORD": (config.metadata_db_config.password),
        }.items()
    }

    if config.metadata_db_provider == "H2":
        new_env["DB_URL"] = "jdbc:h2:" + os.path.abspath(
            os.path.join(settings.rag_databases_dir, "rag")
        )
        new_env.pop("DB_USERNAME", None)
        new_env.pop("DB_PASSWORD", None)

    return new_env


def build_configuration(
    env: dict[str, str], application_config: ApplicationConfig
) -> ProjectConfigPlus:
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
    opensearch_config = OpenSearchConfig(
        opensearch_username=env.get(
            "OPENSEARCH_USERNAME",
        ),
        opensearch_password=env.get("OPENSEARCH_PASSWORD"),
        opensearch_endpoint=env.get("OPENSEARCH_ENDPOINT"),
        opensearch_namespace=env.get("OPENSEARCH_NAMESPACE"),
    )
    validate_config = validate(env)

    return ProjectConfigPlus(
        use_enhanced_pdf_processing=TypeAdapter(bool).validate_python(
            env.get("USE_ENHANCED_PDF_PROCESSING", False),
        ),
        summary_storage_provider=TypeAdapter(
            SummaryStorageProviderType
        ).validate_python(
            env.get("SUMMARY_STORAGE_PROVIDER", "Local"),
        ),
        chat_store_provider=TypeAdapter(ChatStoreProviderType).validate_python(
            env.get("CHAT_STORE_PROVIDER", "Local"),
        ),
        vector_db_provider=TypeAdapter(VectorDbProviderType).validate_python(
            env.get("VECTOR_DB_PROVIDER", "QDRANT")
        ),
        aws_config=aws_config,
        azure_config=azure_config,
        caii_config=caii_config,
        opensearch_config=opensearch_config,
        is_valid_config=validate_config.valid,
        config_validation_results=validate_config,
        release_version=os.environ.get("RELEASE_TAG", "unknown"),
        application_config=application_config,
        openai_config=OpenAiConfig(
            openai_api_key=env.get("OPENAI_API_KEY"),
            openai_api_base=env.get("OPENAI_API_BASE"),
        ),
        cdp_token=env.get("CDP_TOKEN"),
        metadata_db_provider=TypeAdapter(MetadataDbProviderType).validate_python(
            env.get("DB_TYPE", "H2")
        ),
        metadata_db_config=MetadataDbConfig(
            jdbc_url=env.get("DB_URL"),
            username=env.get("DB_USERNAME"),
            password=env.get("DB_PASSWORD"),
        ),
    )


def update_project_environment(new_env: dict[str, str]) -> None:
    try:
        import cmlapi

        client = cmlapi.default_client()
        project_id = settings.cdsw_project_id
        project = client.get_project(project_id=project_id)
        project.environment = json.dumps(new_env)
        client.update_project(project_id=project_id, body=project)
    except ImportError:
        pass


def get_project_environment() -> dict[str, str]:
    try:
        import cmlapi

        client = cmlapi.default_client()
        project_id = settings.cdsw_project_id
        project = client.get_project(project_id=project_id)
        return cast(dict[str, str], json.loads(project.environment))
    except ImportError:
        return dict(os.environ)


class CMLApplication(Protocol):
    name: str
    nvidia_gpu: int
    memory: float


def get_application_config() -> ApplicationConfig:
    """
    Returns the number of GPUs available in the environment.
    """
    try:
        import cmlapi

        client = cmlapi.default_client()
        project_id = settings.cdsw_project_id
        apps = client.list_applications(project_id=project_id)
        ragstudio_app: CMLApplication | None = next(
            (app for app in apps.applications if app.name == "RagStudio"), None
        )
        if ragstudio_app is not None:
            return ApplicationConfig(
                num_of_gpus=ragstudio_app.nvidia_gpu,
                memory_size_gb=ragstudio_app.memory,
            )
    except ImportError:
        pass
    return ApplicationConfig(
        num_of_gpus=0,
        memory_size_gb=0,
    )


def validate_jdbc(
    db_type: MetadataDbProviderType,
    db_url: str,
    password: str,
    username: str,
) -> ValidationResult:
    # Use RAG_STUDIO_INSTALL_DIR to resolve the jar path
    rag_studio_dir = os.getenv("RAG_STUDIO_INSTALL_DIR", "/home/cdsw/rag-studio")
    jar_path = os.path.join(rag_studio_dir, "prebuilt_artifacts/rag-api.jar")
    cmd = [
        f"{os.environ.get('JAVA_HOME')}/bin/java",
        "-cp",
        jar_path,
        "-Dloader.main=com.cloudera.cai.util.db.JdbiUtils",
        "org.springframework.boot.loader.launch.PropertiesLauncher",
        db_url,
        username,
        password,
        str(db_type),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return ValidationResult(valid=True, message=result.stdout.strip())
        elif result.returncode == 2:
            return ValidationResult(
                valid=False, message="Usage error: " + result.stderr.strip()
            )
        else:
            return ValidationResult(valid=False, message=result.stderr.strip())
    except Exception as e:
        return ValidationResult(valid=False, message=str(e))
