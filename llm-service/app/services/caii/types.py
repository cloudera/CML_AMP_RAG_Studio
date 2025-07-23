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
from dataclasses import dataclass
from typing import Dict, Any, Optional

from pydantic import BaseModel, ConfigDict


# class EndpointCondition(BaseModel):
#     status: str
#     severity: str
#     last_transition_time: str
#     reason: str
#     message: str


# class ReplicaMetadata(BaseModel):
#     modelVersion: str
#     replicaCount: int
#     replicaNames: List[str]


# class RegistrySource(BaseModel):
#     model_config = ConfigDict(protected_namespaces=())
#     model_id: Optional[str]
#     version: Optional[int]

# class EndpointStatus(BaseModel):
#     failed_copies: int
#     total_copies: int
#     active_model_state: str
#     target_model_state: str
#     transition_status: str
#


class ListEndpointEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    namespace: str
    name: str
    url: str
    state: str
    created_by: str
    api_standard: str
    has_chat_template: bool
    metric_format: str
    task: Optional[str] = None
    model_name: Optional[str] = None


class Endpoint(ListEndpointEntry):
    model_config = ConfigDict(protected_namespaces=(), extra="ignore")
    # conditions: List[EndpointCondition]
    # status: EndpointStatus
    observed_generation: int
    replica_count: int
    # replica_metadata: List[ReplicaMetadata]
    description: str
    created_at: str
    resources: Dict[str, str]
    # source: Dict[str, RegistrySource]
    autoscaling: Dict[str, Any]
    traffic: Dict[str, str]
    instance_type: str


@dataclass
class ModelResponse:
    model_id: str
    name: str
    available: Optional[bool] = None
    replica_count: Optional[int] = None
    tool_calling_supported: bool = False
