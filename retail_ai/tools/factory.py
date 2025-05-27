"""
Tool Factory

This module provides a centralized factory class for creating and managing all tools
in the Retail AI system. It follows the factory pattern to provide a clean interface
for tool creation and configuration.
"""

from typing import Any, Callable, Optional, Sequence

from langchain_core.language_models import LanguageModelLike
from langchain_core.tools import BaseTool
from loguru import logger
from mlflow.models import ModelConfig

from retail_ai.tools.external import create_genie_tool, search_tool
from retail_ai.tools.inventory import (
    create_find_inventory_by_sku_tool,
    create_find_inventory_by_upc_tool,
    create_find_store_inventory_by_sku_tool,
    create_find_store_inventory_by_upc_tool,
)
from retail_ai.tools.product import (
    create_find_product_by_sku_tool,
    create_find_product_by_upc_tool,
    create_product_classification_tool,
    create_product_comparison_tool,
    create_sku_extraction_tool,
    find_product_details_by_description_tool,
)
from retail_ai.tools.store import (
    create_find_store_by_number_tool,
    create_store_number_extraction_tool,
    find_store_details_by_location_tool,
)
from retail_ai.tools.unity_catalog import create_uc_tools, find_allowable_classifications
from retail_ai.tools.vector_search import create_vector_search_tool


class ToolFactory:
    """
    Factory class for creating and managing Retail AI tools.
    
    This factory provides a centralized interface for creating all types of tools
    used in the Retail AI system, including product tools, inventory tools, store tools,
    and external service tools.
    """

    def __init__(self, model_config: ModelConfig):
        """
        Initialize the tool factory with configuration.
        
        Args:
            model_config: Model configuration containing tool settings
        """
        self.model_config = model_config
        self.logger = logger

    def create_product_tools(
        self, 
        llm: LanguageModelLike,
        warehouse_id: str,
        endpoint_name: str,
        index_name: str,
        columns: Sequence[str],
        k: int = 10
    ) -> dict[str, Any]:
        """
        Create all product-related tools.
        
        Args:
            llm: Language model for LLM-based tools
            warehouse_id: Warehouse ID for Unity Catalog tools
            endpoint_name: Vector search endpoint name
            index_name: Vector search index name
            columns: Columns to include in vector search results
            k: Number of results to return from vector search
            
        Returns:
            Dictionary of product tools
        """
        self.logger.debug("Creating product tools")
        
        # Get allowable classifications
        catalog_name = self.model_config.get("catalog_name")
        database_name = self.model_config.get("database_name")
        classifications = find_allowable_classifications(catalog_name, database_name)
        
        return {
            "product_comparison": create_product_comparison_tool(llm),
            "product_classification": create_product_classification_tool(llm, classifications),
            "sku_extraction": create_sku_extraction_tool(llm),
            "product_search": find_product_details_by_description_tool(
                endpoint_name, index_name, columns, k
            ),
            "find_product_by_sku": create_find_product_by_sku_tool(warehouse_id),
            "find_product_by_upc": create_find_product_by_upc_tool(warehouse_id),
        }

    def create_inventory_tools(self, warehouse_id: str) -> dict[str, Any]:
        """
        Create all inventory-related tools.
        
        Args:
            warehouse_id: Warehouse ID for Unity Catalog tools
            
        Returns:
            Dictionary of inventory tools
        """
        self.logger.debug("Creating inventory tools")
        
        return {
            "find_inventory_by_sku": create_find_inventory_by_sku_tool(warehouse_id),
            "find_inventory_by_upc": create_find_inventory_by_upc_tool(warehouse_id),
            "find_store_inventory_by_sku": create_find_store_inventory_by_sku_tool(warehouse_id),
            "find_store_inventory_by_upc": create_find_store_inventory_by_upc_tool(warehouse_id),
        }

    def create_store_tools(
        self,
        llm: LanguageModelLike,
        warehouse_id: str,
        endpoint_name: str,
        index_name: str,
        columns: Sequence[str],
        k: int = 10
    ) -> dict[str, Any]:
        """
        Create all store-related tools.
        
        Args:
            llm: Language model for LLM-based tools
            warehouse_id: Warehouse ID for Unity Catalog tools
            endpoint_name: Vector search endpoint name
            index_name: Vector search index name
            columns: Columns to include in vector search results
            k: Number of results to return from vector search
            
        Returns:
            Dictionary of store tools
        """
        self.logger.debug("Creating store tools")
        
        catalog_name = self.model_config.get("catalog_name")
        database_name = self.model_config.get("database_name")
        
        return {
            "store_number_extraction": create_store_number_extraction_tool(llm),
            "store_search": find_store_details_by_location_tool(
                endpoint_name, index_name, columns, k
            ),
            "find_store_by_number": create_find_store_by_number_tool(
                catalog_name, database_name, warehouse_id
            ),
        }

    def create_external_tools(self, space_id: Optional[str] = None) -> dict[str, BaseTool]:
        """
        Create all external service tools.
        
        Args:
            space_id: Optional Databricks space ID for Genie
            
        Returns:
            Dictionary of external tools
        """
        self.logger.debug("Creating external tools")
        
        return {
            "genie": create_genie_tool(space_id),
            "web_search": search_tool(self.model_config),
        }

    def create_vector_search_tool_custom(
        self,
        name: str,
        description: str,
        index_name: str,
        **kwargs
    ) -> BaseTool:
        """
        Create a custom vector search tool.
        
        Args:
            name: Tool name
            description: Tool description
            index_name: Vector search index name
            **kwargs: Additional arguments for vector search tool
            
        Returns:
            Vector search tool
        """
        self.logger.debug(f"Creating custom vector search tool: {name}")
        
        return create_vector_search_tool(
            name=name,
            description=description,
            index_name=index_name,
            **kwargs
        )

    def create_unity_catalog_tools(self, function_names: str | Sequence[str]) -> Sequence[BaseTool]:
        """
        Create Unity Catalog function tools.
        
        Args:
            function_names: Function names to create tools for
            
        Returns:
            Sequence of Unity Catalog tools
        """
        self.logger.debug(f"Creating Unity Catalog tools: {function_names}")
        
        return create_uc_tools(function_names)

    def create_all_tools(
        self,
        llm: LanguageModelLike,
        warehouse_id: str,
        product_endpoint_name: str,
        product_index_name: str,
        product_columns: Sequence[str],
        store_endpoint_name: Optional[str] = None,
        store_index_name: Optional[str] = None,
        store_columns: Optional[Sequence[str]] = None,
        space_id: Optional[str] = None,
        k: int = 10
    ) -> dict[str, Any]:
        """
        Create all tools for the Retail AI system.
        
        Args:
            llm: Language model for LLM-based tools
            warehouse_id: Warehouse ID for Unity Catalog tools
            product_endpoint_name: Product vector search endpoint name
            product_index_name: Product vector search index name
            product_columns: Product columns to include in results
            store_endpoint_name: Store vector search endpoint name (optional)
            store_index_name: Store vector search index name (optional)
            store_columns: Store columns to include in results (optional)
            space_id: Optional Databricks space ID for Genie
            k: Number of results to return from vector search
            
        Returns:
            Dictionary containing all tools organized by category
        """
        self.logger.info("Creating all Retail AI tools")
        
        tools = {
            "product": self.create_product_tools(
                llm, warehouse_id, product_endpoint_name, product_index_name, product_columns, k
            ),
            "inventory": self.create_inventory_tools(warehouse_id),
            "external": self.create_external_tools(space_id),
        }
        
        # Add store tools if store search parameters are provided
        if store_endpoint_name and store_index_name and store_columns:
            tools["store"] = self.create_store_tools(
                llm, warehouse_id, store_endpoint_name, store_index_name, store_columns, k
            )
        else:
            # Create store tools without vector search
            catalog_name = self.model_config.get("catalog_name")
            database_name = self.model_config.get("database_name")
            tools["store"] = {
                "store_number_extraction": create_store_number_extraction_tool(llm),
                "find_store_by_number": create_find_store_by_number_tool(
                    catalog_name, database_name, warehouse_id
                ),
            }
        
        self.logger.info(f"Created {sum(len(category) for category in tools.values())} tools")
        return tools 