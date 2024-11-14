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

class DataSourceFile(BaseModel):
    """
    DataSourceFile
    """ # noqa: E501
    id: StrictInt = Field(description="Unique identifier for the file")
    time_created: datetime = Field(description="The date and time when the file was created")
    time_updated: datetime = Field(description="The date and time when the file was last updated")
    created_by_id: StrictStr = Field(description="ID of the user who created the file")
    updated_by_id: StrictStr = Field(description="ID of the user who last updated the file")
    filename: StrictStr = Field(description="Name of the File")
    data_source_id: StrictInt = Field(description="ID of the data source the file belongs to")
    document_id: StrictStr = Field(description="ID of the document in the data source")
    s3_path: StrictStr = Field(description="Path to the file in S3")
    vector_upload_timestamp: datetime = Field(description="The date and time when the file was uploaded")
    size_in_bytes: StrictInt = Field(description="Size of the file in bytes")
    extension: StrictStr = Field(description="Extension of the file")
    summary_creation_timestamp: datetime = Field(description="The date and time when the file summary was created")
    __properties: ClassVar[List[str]] = ["id", "time_created", "time_updated", "created_by_id", "updated_by_id", "filename", "data_source_id", "document_id", "s3_path", "vector_upload_timestamp", "size_in_bytes", "extension", "summary_creation_timestamp"]

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
        """Create an instance of DataSourceFile from a JSON string"""
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
        """Create an instance of DataSourceFile from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "id": obj.get("id"),
            "time_created": obj.get("time_created"),
            "time_updated": obj.get("time_updated"),
            "created_by_id": obj.get("created_by_id"),
            "updated_by_id": obj.get("updated_by_id"),
            "filename": obj.get("filename"),
            "data_source_id": obj.get("data_source_id"),
            "document_id": obj.get("document_id"),
            "s3_path": obj.get("s3_path"),
            "vector_upload_timestamp": obj.get("vector_upload_timestamp"),
            "size_in_bytes": obj.get("size_in_bytes"),
            "extension": obj.get("extension"),
            "summary_creation_timestamp": obj.get("summary_creation_timestamp")
        })
        return _obj


