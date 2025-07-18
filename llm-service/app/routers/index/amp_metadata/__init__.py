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
import subprocess
from subprocess import CompletedProcess
from typing import Annotated

import fastapi
from fastapi import APIRouter, Body
from fastapi.params import Header

from .... import exceptions
from ....config import MetadataDbProviderType
from ....services.amp_metadata import (
    ProjectConfig,
    ProjectConfigPlus,
    config_to_env,
    build_configuration,
    update_project_environment,
    get_project_environment,
    get_application_config,
)
from ....services.amp_update import does_amp_need_updating
from ....services.models.providers import CAIIModelProvider
from ....services.utils import has_admin_rights

router = APIRouter(prefix="/amp", tags=["AMP"])

root_dir = (
    "/home/cdsw/rag-studio" if os.getenv("IS_COMPOSABLE", "") != "" else "/home/cdsw"
)


@router.get("", summary="Returns a boolean for whether AMP needs updating.")
@exceptions.propagates
def amp_up_to_date_status(
    origin_remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> bool:
    if has_admin_rights(origin_remote_user, remote_user_perm):
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


@router.get("/config", summary="Returns application configuration.")
@exceptions.propagates
def get_configuration(
    origin_remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> ProjectConfigPlus:
    env = get_project_environment()
    application_config = get_application_config()

    if has_admin_rights(origin_remote_user, remote_user_perm):
        return build_configuration(env, application_config)

    raise fastapi.HTTPException(
        status_code=401,
        detail="You do not have permission to access application configuration.",
    )


@router.post("/config", summary="Updates application configuration.")
@exceptions.propagates
def update_configuration(
    config: ProjectConfig,
    origin_remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> ProjectConfigPlus:
    if has_admin_rights(origin_remote_user, remote_user_perm):
        if config.cdp_token:
            save_cdp_token(config.cdp_token)
        # merge the new configuration with the existing one
        existing_env = get_project_environment()
        application_config = get_application_config()
        updated_env = config_to_env(config)
        env_to_save = existing_env | updated_env
        update_project_environment(env_to_save)

        return build_configuration(get_project_environment(), application_config)

    raise fastapi.HTTPException(
        status_code=401,
        detail="You do not have permission to access application configuration.",
    )


@router.post("/restart-application", summary="Restarts the application.")
@exceptions.propagates
def restart_application() -> str:
    subprocess.Popen(
        [f"python {root_dir}/scripts/restart_app.py"],
        shell=True,
        start_new_session=True,
    )
    return "OK"


@router.post(
    "/config/cdp-auth-token",
    summary="Saves a CDP auth token for authentication to AI Inference services.",
)
@exceptions.propagates
def save_auth_token(auth_token: Annotated[str, Body(embed=True)]) -> str:
    """
    Saves the provided auth token to /tmp/jwt file in the format expected by caii/utils.py.

    Args:
        auth_token: The authentication token to save

    Returns:
        A success message
    """
    save_cdp_token(auth_token)
    try:
        CAIIModelProvider.list_llm_models()
    except Exception:
        os.remove("cdp_token")
        raise fastapi.HTTPException(
            status_code=400,
            detail="Invalid auth token",
        )

    return "Auth token saved successfully"


@router.post("/validate-jdbc-connection", summary="Validates a JDBC connection string, username, and password.")
@exceptions.propagates
def validate_jdbc_connection(
    db_url: Annotated[str, Body(embed=True)],
    username: Annotated[str, Body(embed=True)],
    password: Annotated[str, Body(embed=True)],
    db_type: Annotated[MetadataDbProviderType, Body(embed=True)],
) -> dict:
    """
    Calls the JdbiUtils main method to validate JDBC connection parameters.
    Returns a dict with 'valid': True/False and 'message'.
    """
    import subprocess
    import os
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
        db_type
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return {"valid": True, "message": result.stdout.strip()}
        elif result.returncode == 2:
            return {"valid": False, "message": "Usage error: " + result.stderr.strip()}
        else:
            return {"valid": False, "message": result.stderr.strip()}
    except Exception as e:
        return {"valid": False, "message": str(e)}


def save_cdp_token(auth_token: str) -> None:
    token_data = {"access_token": auth_token}
    with open("cdp_token", "w") as file:
        json.dump(token_data, file)
