from bson import ObjectId
from pydantic_core import core_schema
from typing import Annotated, Any


class PyObjectId(ObjectId):
    """Custom type for handling MongoDB ObjectId fields with Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, 
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        """Define how to validate and serialize ObjectId."""
        return core_schema.union_schema([
            # First try to validate as ObjectId directly
            core_schema.is_instance_schema(ObjectId),
            # Otherwise, try to parse with ObjectId validator
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
        ])

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value}")
        return ObjectId(value)


# Define a type alias for easier use in models
PydanticObjectId = Annotated[PyObjectId, None]
