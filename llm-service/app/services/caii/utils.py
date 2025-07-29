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
import logging
import os
from typing import Dict, Optional
import requests

from app.config import settings

logger = logging.getLogger(__name__)


def build_auth_headers() -> Dict[str, str]:
    access_token: str = get_caii_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers


def get_caii_access_token() -> str:
    if token_override := settings.cdp_token_override:
        return token_override
    access_token: str
    try:
        with open("cdp_token", "r") as file:
            token_contents = json.load(file)
            access_token = token_contents["access_token"]
            return access_token
    except FileNotFoundError:
        pass

    with open("/tmp/jwt", "r") as file:
        jwt_contents = json.load(file)
    access_token = jwt_contents["access_token"]
    return access_token


def get_cml_version_from_sense_bootstrap() -> Optional[str]:
    """
    Fetches the CML version from the `sense-bootstrap.json` file hosted on the CDSW domain.

    Returns:
        Optional[str]: The CML version if available, otherwise None.
    """
    try:
        url = f"https://{os.environ.get('CDSW_DOMAIN')}/sense-bootstrap.json"
        sense_bootstrap_response = requests.get(url)
        if sense_bootstrap_response.status_code == 200:
            sense_bootstrap_json = sense_bootstrap_response.json()
            version: str = sense_bootstrap_json.get("gitSha")
            return version
        return None
    except Exception as e:
        logger.info(f"Failed to fetch version from `sense-bootstrap.json`. {e}")
        return None
