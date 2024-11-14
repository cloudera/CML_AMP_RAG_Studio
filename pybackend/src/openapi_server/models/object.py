import json
import pprint
from typing import Any, ClassVar, Dict, List

from pydantic import BaseModel, Extra, model_serializer
from pydantic.json import pydantic_encoder


class ObjectModel(BaseModel):
    """
    Base model class that supports additional properties.
    """

    # additional_properties: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        validate_assignment = True
        extra = "forbid"  # Prevent unknown fields from being added to the model

    def _valid_fields(self):
        return {
            k: v for k, v in self.__fields__.items() if k != "additional_properties"
        }

    def __init__(self, **data: Any):
        # Extract known fields and handle additional properties
        known_fields = {key: data[key] for key in self._valid_fields() if key in data}
        additional_props = {
            key: value for key, value in data.items() if key not in self._valid_fields()
        }

        # Initialize the known fields using the BaseModel's init
        super().__init__(**known_fields)

        # Store the additional properties
        self.additional_properties = additional_props

    def __setattr__(self, name, value):
        """Override __setattr__ to store unknown attributes in additional_properties."""
        if name in self._valid_fields() or name == "additional_properties":
            super().__setattr__(name, value)
        else:
            self.additional_properties[name] = value

    def to_str(self) -> str:
        """Returns the string representation of the model using alias."""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias."""
        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.
        This method also includes additional properties.
        """
        _dict = self.model_dump(
            by_alias=True,
            exclude={
                "additional_properties",
            },
            exclude_none=True,
        )
        # Include additional properties in the output dictionary
        if self.additional_properties:
            _dict.update(self.additional_properties)
        return _dict

    @classmethod
    def from_json(cls, json_str: str) -> "ObjectModel":
        """Create an instance of ObjectModel from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_dict(cls, obj: Dict) -> "ObjectModel":
        """Create an instance of ObjectModel from a dict."""
        if obj is None:
            return None

        # Extract known fields dynamically from _valid_fields()
        known_fields = {key: obj[key] for key in cls._valid_fields() if key in obj}

        # Create an instance of the model with known fields
        instance = cls(**known_fields)

        # Store additional fields in additional_properties
        additional_props = {
            key: value for key, value in obj.items() if key not in cls._valid_fields()
        }
        instance.additional_properties = additional_props

        return instance

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Override dict to merge additional_properties"""
        _dict = super().dict(*args, **kwargs)
        if self.additional_properties:
            _dict.update(self.additional_properties)
        return _dict

    def json(self, *args, **kwargs) -> str:
        """Override json to merge additional_properties"""
        _dict = self.to_dict()
        return json.dumps(_dict, default=pydantic_encoder, *args, **kwargs)

    @model_serializer
    def ser_model(self):
        _dict = {}
        for key in self._valid_fields():
            val = getattr(self, key)
            if isinstance(val, BaseModel):
                _dict[key] = val.model_dump()
            else:
                _dict[key] = val
        if self.additional_properties:
            _dict.update(self.additional_properties)
        return _dict
