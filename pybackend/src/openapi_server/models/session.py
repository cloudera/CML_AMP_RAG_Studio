# coding: utf-8

"""
    RAG Studio API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 1.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json




from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr
from typing import Any, ClassVar, Dict, List
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

class Session(BaseModel):
    """
    Session
    """ # noqa: E501
    id: StrictInt
    name: StrictStr
    time_created: datetime = Field(description="Session creation timestamp")
    time_updated: datetime = Field(description="Session update timestamp")
    created_by_id: StrictStr = Field(description="Session creator ID")
    updated_by_id: StrictStr = Field(description="Session updater ID")
    last_interaction_time: datetime = Field(description="Session last interaction timestamp")
    data_source_ids: List[StrictInt]
    __properties: ClassVar[List[str]] = ["id", "name", "time_created", "time_updated", "created_by_id", "updated_by_id", "last_interaction_time", "data_source_ids"]

    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
        "protected_namespaces": (),
    }


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of Session from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        _dict = self.model_dump(
            by_alias=True,
            exclude={
            },
            exclude_none=True,
        )
        return _dict

    @classmethod
    def from_dict(cls, obj: Dict) -> Self:
        """Create an instance of Session from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "id": obj.get("id"),
            "name": obj.get("name"),
            "time_created": obj.get("time_created"),
            "time_updated": obj.get("time_updated"),
            "created_by_id": obj.get("created_by_id"),
            "updated_by_id": obj.get("updated_by_id"),
            "last_interaction_time": obj.get("last_interaction_time"),
            "data_source_ids": obj.get("data_source_ids")
        })
        return _obj


