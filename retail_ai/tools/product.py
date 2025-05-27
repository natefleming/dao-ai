"""
Product Tools

This module contains tool creation functions for product-related operations including
product lookup, classification, comparison, and SKU extraction.
"""

import os
from io import StringIO
from typing import Any, Callable, Literal, Optional, Sequence

import mlflow
import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementResponse, StatementState
from databricks_langchain import DatabricksVectorSearch
from langchain_core.documents import Document
from langchain_core.language_models import LanguageModelLike
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.vectorstores.base import VectorStore
from loguru import logger
from pydantic import BaseModel, Field

from retail_ai.tools.models import ComparisonResult, SkuIdentifier
from unitycatalog.ai.core.base import FunctionExecutionResult, set_uc_function_client


def create_product_comparison_tool(
    llm: LanguageModelLike,
) -> Callable[[str], list[str]]:
    """
    Creates a product comparison tool that can compare multiple products.

    Args:
        llm: The language model to use for comparison analysis

    Returns:
        A callable tool that performs product comparisons
    """
    logger.debug("create_product_comparison_tool")

    # Create the prompt template for product comparison
    comparison_template = """
    You are a retail product comparison expert. Analyze the following products and provide a detailed comparison.
    
    Products to compare:
    {products}
    
    Based on the information provided, compare these products across their features, specifications, price points, 
    and overall value. Identify strengths and weaknesses of each product.
    
    Your analysis should be thorough and objective. Consider various use cases and customer needs.
    """

    prompt = PromptTemplate(
        template=comparison_template,
        input_variables=["products"],
    )

    @tool
    def product_comparison(products: list[dict[str, Any]]) -> ComparisonResult:
        """
        Compare multiple products and provide structured analysis of their features,
        specifications, pros, cons, and recommendations for different user needs.

        Args:
            products: List of product dictionaries to compare. Each product should include
                     at minimum: product_id, product_name, price, and relevant specifications.

        Returns:
            A ComparisonResult object with detailed comparison analysis
        """
        logger.debug(f"product_comparison: {len(products)} products")

        # Format the products for the prompt
        products_str = "\n\n".join(
            [f"Product {i+1}: {str(product)}" for i, product in enumerate(products)]
        )

        # Generate the comparison using the LLM
        chain = prompt | llm.with_structured_output(ComparisonResult)
        result = chain.invoke({"products": products_str})

        return result

    return product_comparison


def create_product_classification_tool(
    llm: LanguageModelLike,
    allowable_classifications: Sequence[str],
    k: int = 1,
) -> Callable[[str], list[str]]:
    """
    Create a tool that classifies products into predefined categories.

    Args:
        llm: Language model to use for classification
        allowable_classifications: List of valid classification categories
        k: Maximum number of classifications to return

    Returns:
        A callable tool function that classifies product descriptions
    """
    logger.debug("create_product_classification_tool")

    class Classifier(BaseModel):
        classifications: list[Literal[tuple(allowable_classifications)]] = Field(
            description=f"The classifications for the product. Must be from: {allowable_classifications}"
        )

    @tool
    def product_classification(input: str) -> list[str]:
        """
        Classify a product description into predefined categories.

        Args:
            input: Product description text to classify

        Returns:
            List of classification categories that apply to the product
        """
        logger.debug(f"product_classification: {input}")

        chain = llm.with_structured_output(Classifier)
        result = chain.invoke(input)

        return result.classifications[:k]

    return product_classification


def create_sku_extraction_tool(llm: LanguageModelLike) -> Callable[[str], str]:
    """
    Create a tool that leverages an LLM to extract SKUs from natural language text.

    In GenAI applications, this tool enables automated extraction of product SKUs from
    customer queries, support tickets, or conversational inputs without requiring
    explicit structured input. This facilitates product lookups and inventory queries
    in conversational AI systems.

    Args:
        llm: Language model to use for SKU extraction from unstructured text

    Returns:
        A callable tool function that extracts a list of SKUs from input text
    """
    logger.debug("create_sku_extraction_tool")

    @tool
    def sku_extraction(input: str) -> list[str]:
        """
        Extract product SKUs from natural language text using an LLM.

        This tool analyzes unstructured text to identify and extract product SKU codes,
        enabling automated product identification from customer conversations or queries.

        Args:
            input: Natural language text that may contain product SKUs

        Returns:
            List of extracted SKU codes found in the input text
        """
        logger.debug(f"sku_extraction: {input}")

        # Use the LLM with structured output to extract SKUs
        chain = llm.with_structured_output(SkuIdentifier)
        result = chain.invoke(
            f"Extract any product SKUs from this text. SKUs are typically 8-12 alphanumeric product codes: {input}"
        )

        return result.skus

    return sku_extraction


def find_product_details_by_description_tool(
    endpoint_name: str,
    index_name: str,
    columns: Sequence[str],
    k: int = 10,
) -> Callable[[str], Sequence[Document]]:
    """
    Create a tool for finding product details using vector search with semantic filtering.

    This factory function generates a specialized search tool that combines semantic vector search
    to find products based on natural language descriptions. It enables natural language product
    discovery for retail applications.

    Args:
        endpoint_name: Name of the Databricks Vector Search endpoint to query
        index_name: Name of the specific vector index containing product information
        columns: List of column names to include in the search results
        k: Maximum number of results to return (default: 10)

    Returns:
        A callable tool function that performs semantic product search
    """
    logger.debug("find_product_details_by_description_tool")

    @tool
    @mlflow.trace(span_type="RETRIEVER", name="vector_search")
    def find_product_details_by_description(content: str) -> Sequence[Document]:
        """
        Find product details using semantic vector search based on natural language descriptions.

        This tool performs semantic search across the product catalog to find items that match
        the provided description, even when exact keywords don't match. It's particularly useful
        for natural language product discovery and recommendation scenarios.

        Args:
            content: Natural language description of the product to search for

        Returns:
            Sequence of Document objects containing matching product information
        """
        logger.debug(f"find_product_details_by_description: {content}")

        # Initialize the vector search client
        vector_search: VectorStore = DatabricksVectorSearch(
            endpoint=endpoint_name,
            index_name=index_name,
            columns=columns,
        )

        # Perform the semantic search
        results: Sequence[Document] = vector_search.similarity_search(
            query=content, k=k
        )

        logger.debug(f"Found {len(results)} product matches")
        return results

    return find_product_details_by_description


def create_find_product_by_sku_tool(warehouse_id: str) -> None:
    """Create a Unity Catalog tool for finding products by SKU."""
    
    @tool
    def find_product_by_sku(skus: list[str]) -> tuple:
        """
        Find product details by one or more SKUs using Unity Catalog functions.
        This tool retrieves detailed information about products based on their SKU codes.

        Args: 
            skus (list[str]): One or more unique identifiers to retrieve. 
                             SKU values are between 8-12 alpha numeric characters.
                             Examples: ["STB-KCP-001", "DUN-KCP-002"]

        Returns: 
            (tuple): A tuple containing product information with fields like:
                product_id BIGINT
                ,sku STRING
                ,upc STRING  
                ,brand_name STRING
                ,product_name STRING
                ,short_description STRING
                ,long_description STRING
                ,merchandise_class STRING
                ,class_cd STRING
                ,department_name STRING
                ,category_name STRING
                ,subcategory_name STRING
                ,base_price DECIMAL(10,2)
                ,msrp DECIMAL(10,2)
        """
        logger.debug(f"find_product_by_sku: {skus}")

        # Convert list to SQL array format
        skus_str = ", ".join([f"'{sku}'" for sku in skus])
        
        # Execute the Unity Catalog function
        sql_query = f"""
            SELECT * FROM nfleming.retail_ai.find_product_by_sku(ARRAY({skus_str}))
        """
        
        # Get workspace client and execute query
        w = WorkspaceClient()
        
        response: StatementResponse = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql_query,
            wait_timeout="30s",
        )

        if response.status.state != StatementState.SUCCEEDED:
            logger.error(f"Query failed: {response.status}")
            return ()

        # Convert results to DataFrame and then to tuple
        if response.result and response.result.data_array:
            df = pd.DataFrame(
                response.result.data_array,
                columns=[col.name for col in response.result.manifest.schema.columns]
            )
            logger.debug(f"Found {len(df)} products")
            return tuple(df.to_dict('records'))
        
        return ()


def create_find_product_by_upc_tool(warehouse_id: str) -> None:
    """Create a Unity Catalog tool for finding products by UPC."""
    
    @tool
    def find_product_by_upc(upcs: list[str]) -> tuple:
        """
        Find product details by one or more UPCs using Unity Catalog functions.
        This tool retrieves detailed information about products based on their UPC codes.

        Args: 
            upcs (list[str]): One or more unique identifiers to retrieve. 
                             UPC values are between 10-16 alpha numeric characters.
                             Examples: ["012345678901", "234567890123"]

        Returns: 
            (tuple): A tuple containing product information with fields like:
                product_id BIGINT
                ,sku STRING
                ,upc STRING
                ,brand_name STRING
                ,product_name STRING
                ,short_description STRING
                ,long_description STRING
                ,merchandise_class STRING
                ,class_cd STRING
                ,department_name STRING
                ,category_name STRING
                ,subcategory_name STRING
                ,base_price DECIMAL(11,2)
                ,msrp DECIMAL(11,2)
        """
        logger.debug(f"find_product_by_upc: {upcs}")

        # Convert list to SQL array format
        upcs_str = ", ".join([f"'{upc}'" for upc in upcs])
        
        # Execute the Unity Catalog function
        sql_query = f"""
            SELECT * FROM nfleming.retail_ai.find_product_by_upc(ARRAY({upcs_str}))
        """
        
        # Get workspace client and execute query
        w = WorkspaceClient()
        
        response: StatementResponse = w.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql_query,
            wait_timeout="30s",
        )

        if response.status.state != StatementState.SUCCEEDED:
            logger.error(f"Query failed: {response.status}")
            return ()

        # Convert results to DataFrame and then to tuple
        if response.result and response.result.data_array:
            df = pd.DataFrame(
                response.result.data_array,
                columns=[col.name for col in response.result.manifest.schema.columns]
            )
            logger.debug(f"Found {len(df)} products")
            return tuple(df.to_dict('records'))
        
        return () 