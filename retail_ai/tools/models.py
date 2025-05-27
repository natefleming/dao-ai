"""
Pydantic Models for Tools

This module contains all Pydantic model definitions used by the tools package.
These models provide structured data validation and serialization for tool inputs and outputs.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProductFeature(BaseModel):
    """A specific feature or attribute of a product for comparison."""

    name: str = Field(description="Name of the feature being compared")
    description: str = Field(
        description="Brief description of what this feature represents"
    )
    importance: int = Field(
        description="Importance rating from 1-10, where 10 is most important"
    )

    model_config = {
        "extra": "forbid",  # This prevents additional properties
        "json_schema_extra": {
            "additionalProperties": False  # Explicitly set in schema
        },
    }


class ProductAttribute(BaseModel):
    """A specific attribute and its value for a product."""

    feature: str = Field(description="Name of the feature/attribute")
    value: str = Field(
        description="The value or description of this attribute for this product"
    )
    rating: Optional[int] = Field(
        None, description="Optional numerical rating (1-10) if applicable"
    )
    pros: list[str] = Field(
        default_factory=list, description="Positive aspects of this attribute"
    )
    cons: list[str] = Field(
        default_factory=list, description="Negative aspects of this attribute"
    )

    model_config = {
        "extra": "forbid",  # This prevents additional properties
        "json_schema_extra": {
            "additionalProperties": False  # Explicitly set in schema
        },
    }


class ProductInfo(BaseModel):
    """Information about a specific product."""

    product_id: str = Field(description="Unique identifier for the product")
    product_name: str = Field(description="Name of the product")
    attributes: list[ProductAttribute] = Field(
        description="List of attributes for this product"
    )
    overall_rating: int = Field(description="Overall rating of the product from 1-10")
    price_value_ratio: int = Field(
        description="Rating of price-to-value ratio from 1-10"
    )
    summary: str = Field(
        description="Brief summary of this product's strengths and weaknesses"
    )

    model_config = {
        "extra": "forbid",  # This prevents additional properties
        "json_schema_extra": {
            "additionalProperties": False  # Explicitly set in schema
        },
    }


class ComparisonResult(BaseModel):
    """The final comparison between multiple products."""

    products: list[ProductInfo] = Field(description="List of products being compared")
    key_features: list[ProductFeature] = Field(
        description="Key features that were compared"
    )
    winner: Optional[str] = Field(
        None, description="Product ID of the overall winner, if there is one"
    )
    best_value: Optional[str] = Field(
        None, description="Product ID with the best value for money"
    )
    comparison_summary: str = Field(
        description="Overall summary of the comparison results"
    )
    recommendations: list[str] = Field(
        description="Recommendations for different user needs/scenarios"
    )

    model_config = {
        "extra": "forbid",  # This prevents additional properties
        "json_schema_extra": {
            "additionalProperties": False  # Explicitly set in schema
        },
    }


class StoreInfo(BaseModel):
    """Information about store numbers extracted from text."""

    store_numbers: list[str] = Field(
        default_factory=list,
        description="The store numbers mentioned in the text. Typically 3-4 digit numeric values."
    )

    model_config = {
        "extra": "forbid",  # This prevents additional properties
        "json_schema_extra": {
            "additionalProperties": False  # Explicitly set in schema
        },
    }


class SkuIdentifier(BaseModel):
    """Information about SKUs extracted from text."""

    skus: list[str] = Field(
        default_factory=list,
        description="The SKUs mentioned in the text. Typically 8-12 alphanumeric characters."
    )

    model_config = {
        "extra": "forbid",  # This prevents additional properties
        "json_schema_extra": {
            "additionalProperties": False  # Explicitly set in schema
        },
    } 