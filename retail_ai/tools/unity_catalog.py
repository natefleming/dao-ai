"""
Unity Catalog Tools

This module contains tool creation functions for Unity Catalog integration including
function toolkit creation and classification management.
"""

from typing import Optional, Sequence

from databricks.sdk import WorkspaceClient
from databricks_langchain import DatabricksFunctionClient, UCFunctionToolkit
from langchain_core.tools import BaseTool
from loguru import logger
from unitycatalog.ai.core.base import set_uc_function_client


def find_allowable_classifications(
    catalog_name: str, database_name: str, w: Optional[WorkspaceClient] = None
) -> Sequence[str]:
    """
    Retrieve allowable product classifications from Unity Catalog.

    This function queries the Unity Catalog to get the list of valid product
    classifications that can be used for product categorization.

    Args:
        catalog_name: Name of the Unity Catalog catalog
        database_name: Name of the database within the catalog
        w: Optional WorkspaceClient instance (will create one if not provided)

    Returns:
        Sequence of valid classification strings
    """
    logger.debug("find_allowable_classifications")

    if w is None:
        w = WorkspaceClient()

    try:
        # Query the classifications table or function
        # This is a placeholder - implement based on your actual schema
        classifications = [
            "Electronics",
            "Home & Garden", 
            "Sports & Outdoors",
            "Tools & Hardware",
            "Automotive",
            "Health & Beauty",
            "Clothing & Accessories",
            "Food & Beverages",
            "Books & Media",
            "Toys & Games"
        ]
        
        logger.debug(f"Found {len(classifications)} classifications")
        return classifications
        
    except Exception as e:
        logger.error(f"Failed to retrieve classifications: {e}")
        return []


def create_uc_tools(function_names: str | Sequence[str]) -> Sequence[BaseTool]:
    """
    Create Unity Catalog function tools from function names.

    This function creates LangChain tools from Unity Catalog functions,
    enabling them to be used within agent workflows.

    Args:
        function_names: Single function name or sequence of function names to create tools for

    Returns:
        Sequence of BaseTool instances for the specified UC functions
    """
    logger.debug(f"create_uc_tools: {function_names}")

    try:
        # Ensure function_names is a sequence
        if isinstance(function_names, str):
            function_names = [function_names]

        # Create the UC function client
        client = DatabricksFunctionClient()
        set_uc_function_client(client)

        # Create the toolkit with specified functions
        toolkit = UCFunctionToolkit(
            function_names=list(function_names),
            client=client
        )

        # Get the tools from the toolkit
        tools = toolkit.get_tools()
        
        logger.debug(f"Created {len(tools)} UC tools")
        return tools

    except Exception as e:
        logger.error(f"Failed to create UC tools: {e}")
        return [] 