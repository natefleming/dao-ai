"""
Vector Search Tools

This module contains tool creation functions for vector search operations including
generic vector search tool creation and configuration.
"""

from typing import Sequence

from databricks_langchain.vector_search_retriever_tool import VectorSearchRetrieverTool
from langchain_core.tools import BaseTool
from loguru import logger


def create_vector_search_tool(
    name: str,
    description: str,
    index_name: str,
    primary_key: str = "id",
    text_column: str = "content",
    doc_uri: str = "doc_uri",
    columns: Sequence[str] = None,
    search_parameters: dict[str, str] = {},
) -> BaseTool:
    """
    Create a vector search tool for semantic search operations.

    This function creates a LangChain tool that can perform vector search operations
    against a Databricks Vector Search index, enabling semantic search capabilities
    within agent workflows.

    Args:
        name: Name of the tool
        description: Description of what the tool does
        index_name: Name of the vector search index to query
        primary_key: Primary key column name (default: "id")
        text_column: Text content column name (default: "content")
        doc_uri: Document URI column name (default: "doc_uri")
        columns: List of columns to include in results
        search_parameters: Additional search parameters

    Returns:
        A BaseTool instance for vector search operations
    """
    logger.debug(f"create_vector_search_tool: {name}")

    try:
        # Create the vector search retriever tool
        tool = VectorSearchRetrieverTool(
            name=name,
            description=description,
            index_name=index_name,
            primary_key=primary_key,
            text_column=text_column,
            doc_uri=doc_uri,
            columns=columns or [],
            search_parameters=search_parameters,
        )
        
        logger.debug(f"Created vector search tool: {name}")
        return tool

    except Exception as e:
        logger.error(f"Failed to create vector search tool {name}: {e}")
        raise 