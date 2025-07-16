import graphene
from graphql import GraphQLError
from pydantic import BaseModel, field_validator
from typing import List

# Step 1: Define Pydantic Model for Validation (Updated for Pydantic v2)
class CreateStorySchema(BaseModel):
    title: str
    content: str
    captions: str
    privacy: List[str]
    

    @field_validator("privacy", mode="before")
    @classmethod
    def validate_privacy(cls, value):
        allowed_values = {"Inner", "Outer", "Universe"}
        if not isinstance(value, list) or not all(item in allowed_values for item in value):
            raise GraphQLError(f"Privacy must be one or more of {allowed_values}")
        return value

    
