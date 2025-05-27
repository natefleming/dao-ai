"""
Inventory Tools

This module contains tool creation functions for inventory-related operations including
inventory lookup by SKU/UPC and store-specific inventory queries.
"""

import pandas as pd
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementResponse, StatementState
from langchain_core.tools import tool
from loguru import logger


def create_find_inventory_by_sku_tool(warehouse_id: str) -> None:
    """Create a Unity Catalog tool for finding inventory by SKU."""
    
    @tool
    def find_inventory_by_sku(skus: list[str]) -> tuple:
        """
        Find inventory details by one or more SKUs using Unity Catalog functions.
        This tool retrieves detailed inventory information across all stores for products based on their SKU codes.

        Args: 
            skus (list[str]): One or more unique identifiers to retrieve. 
                             SKU values are between 5-8 alpha numeric characters.
                             Examples: ["PET-KCP-001", "DUN-KCP-002"]

        Returns: 
            (tuple): A tuple containing inventory information with fields like:
                inventory_id BIGINT
                ,sku STRING
                ,upc STRING
                ,product_id BIGINT
                ,store_id INT
                ,store_quantity INT
                ,warehouse STRING
                ,warehouse_quantity INT
                ,retail_amount DECIMAL(11, 2)
                ,popularity_rating STRING
                ,department STRING
                ,aisle_location STRING
                ,is_closeout BOOLEAN
        """
        logger.debug(f"find_inventory_by_sku: {skus}")

        # Convert list to SQL array format
        skus_str = ", ".join([f"'{sku}'" for sku in skus])
        
        # Execute the Unity Catalog function
        sql_query = f"""
            SELECT * FROM nfleming.retail_ai.find_inventory_by_sku(ARRAY({skus_str}))
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
            logger.debug(f"Found {len(df)} inventory records")
            return tuple(df.to_dict('records'))
        
        return ()


def create_find_inventory_by_upc_tool(warehouse_id: str) -> None:
    """Create a Unity Catalog tool for finding inventory by UPC."""
    
    @tool
    def find_inventory_by_upc(upcs: list[str]) -> tuple:
        """
        Find inventory details by one or more UPCs using Unity Catalog functions.
        This tool retrieves detailed inventory information across all stores for products based on their UPC codes.

        Args: 
            upcs (list[str]): One or more unique identifiers to retrieve. 
                             UPC values are between 10-16 alpha numeric characters.
                             Examples: ["123456789012", "234567890123"]

        Returns: 
            (tuple): A tuple containing inventory information with fields like:
                inventory_id BIGINT
                ,sku STRING
                ,upc STRING
                ,product_id BIGINT
                ,store_id INT
                ,store_quantity INT
                ,warehouse STRING
                ,warehouse_quantity INT
                ,retail_amount DECIMAL(11, 2)
                ,popularity_rating STRING
                ,department STRING
                ,aisle_location STRING
                ,is_closeout BOOLEAN
        """
        logger.debug(f"find_inventory_by_upc: {upcs}")

        # Convert list to SQL array format
        upcs_str = ", ".join([f"'{upc}'" for upc in upcs])
        
        # Execute the Unity Catalog function
        sql_query = f"""
            SELECT * FROM nfleming.retail_ai.find_inventory_by_upc(ARRAY({upcs_str}))
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
            logger.debug(f"Found {len(df)} inventory records")
            return tuple(df.to_dict('records'))
        
        return ()


def create_find_store_inventory_by_sku_tool(warehouse_id: str) -> None:
    """Create a Unity Catalog tool for finding store-specific inventory by SKU."""
    
    @tool
    def find_store_inventory_by_sku(store: str, skus: list[str]) -> tuple:
        """
        Find store-specific inventory details by one or more SKUs using Unity Catalog functions.
        This tool retrieves detailed inventory information for a specific store based on SKU codes.

        Args: 
            store (str): The store identifier to retrieve inventory for
            skus (list[str]): One or more unique identifiers to retrieve. 
                             SKU values are between 5-8 alpha numeric characters.
                             Examples: ["PET-KCP-001", "DUN-KCP-002"]

        Returns: 
            (tuple): A tuple containing store-specific inventory information with fields like:
                inventory_id BIGINT
                ,sku STRING
                ,upc STRING
                ,product_id BIGINT
                ,store_id INT
                ,store_quantity INT
                ,warehouse STRING
                ,warehouse_quantity INT
                ,retail_amount DECIMAL(11, 2)
                ,popularity_rating STRING
                ,department STRING
                ,aisle_location STRING
                ,is_closeout BOOLEAN
        """
        logger.debug(f"find_store_inventory_by_sku: store={store}, skus={skus}")

        # Convert list to SQL array format
        skus_str = ", ".join([f"'{sku}'" for sku in skus])
        
        # Execute the Unity Catalog function
        sql_query = f"""
            SELECT * FROM nfleming.retail_ai.find_store_inventory_by_sku({store}, ARRAY({skus_str}))
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
            logger.debug(f"Found {len(df)} store inventory records")
            return tuple(df.to_dict('records'))
        
        return ()


def create_find_store_inventory_by_upc_tool(warehouse_id: str) -> None:
    """Create a Unity Catalog tool for finding store-specific inventory by UPC."""
    
    @tool
    def find_store_inventory_by_upc(store: str, upcs: list[str]) -> tuple:
        """
        Find store-specific inventory details by one or more UPCs using Unity Catalog functions.
        This tool retrieves detailed inventory information for a specific store based on UPC codes.

        Args: 
            store (str): The store identifier to retrieve inventory for
            upcs (list[str]): One or more unique identifiers to retrieve. 
                             UPC values are between 10-16 alpha numeric characters.
                             Examples: ["123456789012", "234567890123"]

        Returns: 
            (tuple): A tuple containing store-specific inventory information with fields like:
                inventory_id BIGINT
                ,sku STRING
                ,upc STRING
                ,product_id BIGINT
                ,store_id INT
                ,store_quantity INT
                ,warehouse STRING
                ,warehouse_quantity INT
                ,retail_amount DECIMAL(11, 2)
                ,popularity_rating STRING
                ,department STRING
                ,aisle_location STRING
                ,is_closeout BOOLEAN
        """
        logger.debug(f"find_store_inventory_by_upc: store={store}, upcs={upcs}")

        # Convert list to SQL array format
        upcs_str = ", ".join([f"'{upc}'" for upc in upcs])
        
        # Execute the Unity Catalog function
        sql_query = f"""
            SELECT * FROM nfleming.retail_ai.find_store_inventory_by_upc({store}, ARRAY({upcs_str}))
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
            logger.debug(f"Found {len(df)} store inventory records")
            return tuple(df.to_dict('records'))
        
        return () 