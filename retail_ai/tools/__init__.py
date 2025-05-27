"""
Tools Package

This package contains all tool creation functions and utilities for the Retail AI system.
Tools are organized by category: product tools, inventory tools, store tools, etc.
"""

from retail_ai.tools.factory import ToolFactory
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
from retail_ai.tools.external import (
    create_genie_tool,
    search_tool,
)
from retail_ai.tools.vector_search import (
    create_vector_search_tool,
)
from retail_ai.tools.unity_catalog import (
    create_uc_tools,
    find_allowable_classifications,
)

__all__ = [
    # Factory
    "ToolFactory",
    
    # Product tools
    "create_find_product_by_sku_tool",
    "create_find_product_by_upc_tool", 
    "create_product_classification_tool",
    "create_product_comparison_tool",
    "create_sku_extraction_tool",
    "find_product_details_by_description_tool",
    
    # Inventory tools
    "create_find_inventory_by_sku_tool",
    "create_find_inventory_by_upc_tool",
    "create_find_store_inventory_by_sku_tool", 
    "create_find_store_inventory_by_upc_tool",
    
    # Store tools
    "create_find_store_by_number_tool",
    "create_store_number_extraction_tool",
    "find_store_details_by_location_tool",
    
    # External tools
    "create_genie_tool",
    "search_tool",
    
    # Vector search tools
    "create_vector_search_tool",
    
    # Unity Catalog tools
    "create_uc_tools",
    "find_allowable_classifications",
] 