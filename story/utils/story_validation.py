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

    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        if not value or not value.strip():
            raise GraphQLError("Title cannot be empty")
        if len(value.strip()) > 50:
            raise GraphQLError("Title cannot exceed 50 characters")
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value):
        if not value or not value.strip():
            raise GraphQLError("Content cannot be empty")
        if len(value.strip()) > 50:
            raise GraphQLError("Content cannot exceed 50 characters")
        return value

    @field_validator("captions")
    @classmethod
    def validate_captions(cls, value):
        if not value or not value.strip():
            raise GraphQLError("Captions cannot be empty")
        if len(value.strip()) > 100:
            raise GraphQLError("Captions cannot exceed 100 characters")
        return value

    @field_validator("privacy", mode="before")
    @classmethod
    def validate_privacy(cls, value):
        allowed_values = {"Inner", "Outer", "Universe"}

        # Handle case where value is not a list (e.g., single string)
        if isinstance(value, str):
            value = [value]
        elif not isinstance(value, list):
            raise GraphQLError("Privacy must be a list or a string.")

        # Validate that all values are in allowed set
        if not all(item in allowed_values for item in value):
            raise GraphQLError(f"Privacy must be one or more of {allowed_values}")

        return value
