# Databricks notebook source
# MAGIC %pip install --quiet uv
# MAGIC
# MAGIC import os
# MAGIC os.environ["UV_PROJECT_ENVIRONMENT"] = os.environ["VIRTUAL_ENV"]

# COMMAND ----------

# MAGIC %sh uv --project ../ sync

# COMMAND ----------

# MAGIC %restart_python

# COMMAND ----------

import logging
logging.getLogger("py4j").setLevel(logging.WARNING)

# COMMAND ----------

dbutils.widgets.text(name="config-path", defaultValue="../config/model_config.yaml")
config_path: str = dbutils.widgets.get("config-path")
print(config_path)

# COMMAND ----------

import sys

sys.path.insert(0, "..")

# COMMAND ----------

from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())

# COMMAND ----------

from typing import Any, Dict, Optional, List

from mlflow.models import ModelConfig
from retail_ai.config import AppConfig, SchemaModel

model_config_file: str = config_path
model_config: ModelConfig = ModelConfig(development_config=model_config_file)
config: AppConfig = AppConfig(**model_config.to_dict())

schema: SchemaModel = config.schemas.get("dais_schema")
catalog_name: str = schema.catalog_name
schema_name: str = schema.schema_name


print(f"catalog_name: {catalog_name}")
print(f"schema_name: {schema_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Unity Catalog Tools for Retail AI
# MAGIC
# MAGIC This notebook creates Unity Catalog functions for the Retail AI system to provide:
# MAGIC - Product lookup by SKU and UPC
# MAGIC - Inventory management across stores and warehouses
# MAGIC - Store-specific inventory queries
# MAGIC - Store information and location services with vector search capabilities
# MAGIC
# MAGIC ## Functions Created:
# MAGIC 1. `find_product_by_sku` - Product details by SKU
# MAGIC 2. `find_product_by_upc` - Product details by UPC
# MAGIC 3. `find_inventory_by_sku` - Inventory across all stores by SKU
# MAGIC 4. `find_inventory_by_upc` - Inventory across all stores by UPC
# MAGIC 5. `find_store_inventory_by_sku` - Store-specific inventory by SKU
# MAGIC 6. `find_store_inventory_by_upc` - Store-specific inventory by UPC
# MAGIC 7. `find_store_by_number` - Store details by store ID (updated for dim_store)
# MAGIC 8. `find_stores_by_location` - Vector search for stores by location description

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

import logging
import pandas as pd
from io import StringIO
from typing import Any, Dict, Optional, List, Tuple, Union

from dotenv import find_dotenv, load_dotenv
from mlflow.models import ModelConfig
from databricks.sdk import WorkspaceClient
from unitycatalog.ai.core.databricks import DatabricksFunctionClient
from unitycatalog.ai.core.base import FunctionExecutionResult

# Databricks LangChain imports
try:
    from databricks_langchain import DatabricksFunctionClient, UCFunctionToolkit, DatabricksVectorSearch
except ImportError:
    print("Warning: databricks_langchain not available")
    DatabricksVectorSearch = None

# LangChain core imports
try:
    from langchain_core.documents import Document
    from langchain_core.vectorstores.base import VectorStore
except ImportError:
    print("Warning: langchain_core not available")
    Document = None
    VectorStore = None

# Load environment variables
_ = load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration and Client Setup

# COMMAND ----------

def setup_configuration() -> Tuple[str, str, WorkspaceClient, DatabricksFunctionClient]:
    """
    Set up configuration and clients for Unity Catalog operations.
    
    Returns:
        Tuple containing catalog_name, database_name, workspace_client, and function_client
    """
    try:
        
        if not catalog_name or not schema_name:
            raise ValueError("catalog_name and schema_name must be specified in model_config.yaml")
        
        logger.info(f"Using catalog: {catalog_name}, database: {schema_name}")
        
        # Initialize clients
        workspace_client = WorkspaceClient()
        function_client = DatabricksFunctionClient(client=workspace_client)
        
        return catalog_name, schema_name, workspace_client, function_client
        
    except Exception as e:
        logger.error(f"Failed to setup configuration: {e}")
        raise

# Initialize configuration and clients
catalog_name, database_name, w, client = setup_configuration()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Utility Functions

# COMMAND ----------

def execute_and_display_function(
    client: DatabricksFunctionClient,
    function_name: str,
    parameters: Dict[str, Any],
    description: str = ""
) -> pd.DataFrame:
    """
    Execute a Unity Catalog function and display results.
    
    Args:
        client: DatabricksFunctionClient instance
        function_name: Full name of the function to execute
        parameters: Parameters to pass to the function
        description: Optional description for logging
        
    Returns:
        DataFrame with function results
        
    Raises:
        Exception: If function execution fails
    """
    try:
        logger.info(f"Executing function: {function_name} with parameters: {parameters}")
        if description:
            logger.info(f"Description: {description}")
            
        result: FunctionExecutionResult = client.execute_function(
            function_name=function_name,
            parameters=parameters
        )
        
        if result.error:
            logger.error(f"Function execution failed: {result.error}")
            raise Exception(f"Function execution error: {result.error}")
        
        # Handle empty results
        if not result.value or result.value.strip() == "":
            logger.warning(f"Function {function_name} returned empty result")
            print(f"⚠️  Function {function_name} returned no data. This might indicate:")
            print(f"   - The table {function_name.split('.')[-1]} doesn't exist or is empty")
            print(f"   - The search parameters {parameters} don't match any records")
            print(f"   - The data hasn't been loaded into the table yet")
            return pd.DataFrame()
        
        # Convert result to DataFrame
        try:
            df = pd.read_csv(StringIO(result.value))
            logger.info(f"Function executed successfully. Returned {len(df)} rows.")
            
            # Display results in Databricks if not empty
            if not df.empty:
                display(df)
            else:
                print(f"✅ Function executed successfully but returned 0 rows")
                print(f"   Parameters used: {parameters}")
            
            return df
            
        except pd.errors.EmptyDataError:
            logger.warning(f"Function {function_name} returned empty CSV data")
            print(f"⚠️  Function {function_name} executed but returned no data")
            return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Error executing function {function_name}: {e}")
        print(f"❌ Error executing function {function_name}: {str(e)}")
        raise

def create_function_safely(
    client: DatabricksFunctionClient,
    sql_function_body: str,
    function_name: str,
    description: str = ""
) -> None:
    """
    Create a Unity Catalog function with error handling.
    
    Args:
        client: DatabricksFunctionClient instance
        sql_function_body: SQL DDL for the function
        function_name: Name of the function being created
        description: Optional description for logging
    """
    try:
        logger.info(f"Creating function: {function_name}")
        if description:
            logger.info(f"Description: {description}")
            
        client.create_function(sql_function_body=sql_function_body)
        logger.info(f"Successfully created function: {function_name}")
        
    except Exception as e:
        logger.error(f"Failed to create function {function_name}: {e}")
        raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Product Lookup Functions

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Product Lookup by SKU Function

# COMMAND ----------

def create_find_product_by_sku_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create the find_product_by_sku Unity Catalog function."""
    
    function_name = f"{catalog_name}.{database_name}.find_product_by_sku"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  sku ARRAY<STRING> COMMENT 'One or more unique identifiers for retrieve. It may help to use another tool to provide this value. SKU values are between 8-12 alpha numeric characters'
)
RETURNS TABLE(
  product_id BIGINT COMMENT 'Unique identifier for each product in the catalog' 
  ,sku STRING COMMENT 'Stock Keeping Unit - unique internal product identifier code'
  ,upc STRING COMMENT 'Universal Product Code - standardized barcode number for product identification'
  ,brand_name STRING COMMENT 'Name of the manufacturer or brand that produces the product'
  ,product_name STRING COMMENT 'Display name of the product as shown to customers'
  ,short_description STRING COMMENT 'Brief description of the product'
  ,long_description STRING COMMENT 'Detailed text description of the product including key features and attributes'
  ,merchandise_class STRING COMMENT 'Broad category classification of the product (e.g., Beverages)'
  ,class_cd STRING COMMENT 'Alphanumeric code representing the specific product subcategory'
  ,department_name STRING COMMENT 'Name of the department the product belongs to'
  ,category_name STRING COMMENT 'Name of the category the product belongs to'
  ,subcategory_name STRING COMMENT 'Name of the subcategory the product belongs to'
  ,base_price DOUBLE COMMENT 'Base price of the product'
  ,msrp DOUBLE COMMENT 'MSRP (Manufacturer Suggested Retail Price)'
)
READS SQL DATA
COMMENT 'Retrieves detailed information about a specific product by its SKU. This function is designed for product information retrieval in retail applications and can be used for product information, comparison, and recommendation.'
RETURN 
SELECT 
  product_id
  ,sku
  ,upc
  ,brand_name
  ,product_name
  ,short_description
  ,long_description
  ,merchandise_class
  ,class_cd
  ,department_name
  ,category_name
  ,subcategory_name
  ,base_price
  ,msrp
FROM {catalog_name}.{database_name}.products 
WHERE ARRAY_CONTAINS(find_product_by_sku.sku, sku)
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to retrieve product details by SKU"
    )

# Create the function
create_find_product_by_sku_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Product Lookup by SKU

# COMMAND ----------

# Test the find_product_by_sku function
test_df = execute_and_display_function(
    client=client,
    function_name=f"{catalog_name}.{database_name}.find_product_by_sku",
    parameters={"sku": ["STB-KCP-001"]},
    description="Testing product lookup by SKU"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Product Lookup by UPC Function

# COMMAND ----------

def create_find_product_by_upc_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create the find_product_by_upc Unity Catalog function."""
    
    function_name = f"{catalog_name}.{database_name}.find_product_by_upc"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  upc ARRAY<STRING> COMMENT 'One or more unique identifiers to retrieve. UPC values are between 10-16 alphanumeric characters'
)
RETURNS TABLE(
  product_id BIGINT COMMENT 'Unique identifier for each product in the catalog'
  ,sku STRING COMMENT 'Stock Keeping Unit - unique internal product identifier code'
  ,upc STRING COMMENT 'Universal Product Code - standardized barcode number for product identification'
  ,brand_name STRING COMMENT 'Name of the manufacturer or brand that produces the product'
  ,product_name STRING COMMENT 'Display name of the product as shown to customers'
  ,short_description STRING COMMENT 'Brief product description for quick reference'
  ,long_description STRING COMMENT 'Detailed text description of the product including key features and attributes'
  ,merchandise_class STRING COMMENT 'Broad category classification of the product (e.g., Electronics, Apparel, Grocery)'
  ,class_cd STRING COMMENT 'Alphanumeric code representing the specific product subcategory'
  ,department_name STRING COMMENT 'Name of the department where product is typically located'
  ,category_name STRING COMMENT 'Name of the product category'
  ,subcategory_name STRING COMMENT 'Name of the product subcategory'
  ,base_price DOUBLE COMMENT 'Standard retail price before any discounts'
  ,msrp DOUBLE COMMENT 'MSRP (Manufacturer Suggested Retail Price)'
)
READS SQL DATA
COMMENT 'Retrieves detailed information about specific products by their UPC. This function is designed for product information retrieval in retail applications and can be used for product information, comparison, and recommendation.'
RETURN 
SELECT 
  product_id
  ,sku
  ,upc
  ,brand_name
  ,product_name
  ,short_description
  ,long_description
  ,merchandise_class
  ,class_cd
  ,department_name
  ,category_name
  ,subcategory_name
  ,base_price
  ,msrp
FROM {catalog_name}.{database_name}.products 
WHERE ARRAY_CONTAINS(find_product_by_upc.upc, upc)
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to retrieve product details by UPC"
    )

# Create the function
create_find_product_by_upc_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Product Lookup by UPC

# COMMAND ----------

# Test the find_product_by_upc function
test_df = execute_and_display_function(
    client=client,
    function_name=f"{catalog_name}.{database_name}.find_product_by_upc",
    parameters={"upc": ["012345678901"]},
    description="Testing product lookup by UPC"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Inventory Management Functions

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Inventory Lookup by SKU Function

# COMMAND ----------

def create_find_inventory_by_sku_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create the find_inventory_by_sku Unity Catalog function."""
    
    function_name = f"{catalog_name}.{database_name}.find_inventory_by_sku"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  sku ARRAY<STRING> COMMENT 'One or more unique identifiers for retrieve. It may help to use another tool to provide this value. SKU values are between 5-8 alpha numeric characters'
)
RETURNS TABLE(
  inventory_id BIGINT COMMENT 'Unique identifier for each inventory record'
  ,sku STRING COMMENT 'Stock Keeping Unit - unique internal product identifier code'
  ,upc STRING COMMENT 'Universal Product Code - standardized barcode number for product identification'
  ,product_id BIGINT COMMENT 'Foreign key reference to the product table identifying the specific product'  
  ,store_id INT COMMENT 'Store identifier where inventory is located'
  ,store_quantity INT COMMENT 'Current available quantity of product in the specified store'
  ,warehouse STRING COMMENT 'Warehouse identifier where backup inventory is stored'
  ,warehouse_quantity INT COMMENT 'Current available quantity of product in the specified warehouse'
  ,retail_amount DOUBLE COMMENT 'Current retail price of the product'
  ,popularity_rating STRING COMMENT 'Rating indicating how popular/frequently purchased the product is (e.g., high, medium, low)'
  ,department STRING COMMENT 'Department within the store where the product is categorized'
  ,aisle_location STRING COMMENT 'Physical aisle location identifier where the product can be found in store'
  ,is_closeout BOOLEAN COMMENT 'Flag indicating whether the product is marked for closeout/clearance'
)
READS SQL DATA
COMMENT 'Retrieves detailed inventory information for products by SKU across all stores. This function is designed for inventory management in retail applications.'
RETURN 
SELECT 
  inventory_id
  ,sku
  ,upc
  ,inventory.product_id
  ,store_id
  ,store_quantity
  ,warehouse
  ,warehouse_quantity
  ,retail_amount
  ,popularity_rating
  ,department
  ,aisle_location
  ,is_closeout
FROM {catalog_name}.{database_name}.inventory inventory
JOIN {catalog_name}.{database_name}.products products
ON inventory.product_id = products.product_id
WHERE ARRAY_CONTAINS(find_inventory_by_sku.sku, products.sku)
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to retrieve inventory details by SKU across all stores"
    )

# Create the function
create_find_inventory_by_sku_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Inventory Lookup by SKU

# COMMAND ----------

# Test the find_inventory_by_sku function
test_df = execute_and_display_function(
    client=client,
    function_name=f"{catalog_name}.{database_name}.find_inventory_by_sku",
    parameters={"sku": ["PET-KCP-001"]},
    description="Testing inventory lookup by SKU"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Inventory Lookup by UPC Function

# COMMAND ----------

def create_find_inventory_by_upc_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create the find_inventory_by_upc Unity Catalog function."""
    
    function_name = f"{catalog_name}.{database_name}.find_inventory_by_upc"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  upc ARRAY<STRING> COMMENT 'One or more unique identifiers for retrieve. It may help to use another tool to provide this value. UPC values are between 10-16 alpha numeric characters'
)
RETURNS TABLE(
  inventory_id BIGINT COMMENT 'Unique identifier for each inventory record'
  ,sku STRING COMMENT 'Stock Keeping Unit - unique internal product identifier code'
  ,upc STRING COMMENT 'Universal Product Code - standardized barcode number for product identification'
  ,product_id BIGINT COMMENT 'Foreign key reference to the product table identifying the specific product'  
  ,store_id INT COMMENT 'Store identifier where inventory is located'
  ,store_quantity INT COMMENT 'Current available quantity of product in the specified store'
  ,warehouse STRING COMMENT 'Warehouse identifier where backup inventory is stored'
  ,warehouse_quantity INT COMMENT 'Current available quantity of product in the specified warehouse'
  ,retail_amount DOUBLE COMMENT 'Current retail price of the product'
  ,popularity_rating STRING COMMENT 'Rating indicating how popular/frequently purchased the product is (e.g., high, medium, low)'
  ,department STRING COMMENT 'Department within the store where the product is categorized'
  ,aisle_location STRING COMMENT 'Physical aisle location identifier where the product can be found in store'
  ,is_closeout BOOLEAN COMMENT 'Flag indicating whether the product is marked for closeout/clearance'
)
READS SQL DATA
COMMENT 'Retrieves detailed inventory information for products by UPC across all stores. This function is designed for inventory management in retail applications.'
RETURN 
SELECT 
  inventory_id
  ,sku
  ,upc
  ,inventory.product_id
  ,store_id
  ,store_quantity
  ,warehouse
  ,warehouse_quantity
  ,retail_amount
  ,popularity_rating
  ,department
  ,aisle_location
  ,is_closeout
FROM {catalog_name}.{database_name}.inventory inventory
JOIN {catalog_name}.{database_name}.products products
ON inventory.product_id = products.product_id
WHERE ARRAY_CONTAINS(find_inventory_by_upc.upc, products.upc)
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to retrieve inventory details by UPC across all stores"
    )

# Create the function
create_find_inventory_by_upc_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Inventory Lookup by UPC

# COMMAND ----------

# Test the find_inventory_by_upc function
test_df = execute_and_display_function(
    client=client,
    function_name=f"{catalog_name}.{database_name}.find_inventory_by_upc",
    parameters={"upc": ["123456789012"]},
    description="Testing inventory lookup by UPC"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Store-Specific Inventory Functions

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Store Inventory Lookup by SKU Function

# COMMAND ----------

def create_find_store_inventory_by_sku_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create the find_store_inventory_by_sku Unity Catalog function."""
    
    function_name = f"{catalog_name}.{database_name}.find_store_inventory_by_sku"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  store_id INT COMMENT 'The store identifier to retrieve inventory for'
  ,sku ARRAY<STRING> COMMENT 'One or more unique identifiers to retrieve. It may help to use another tool to provide this value. SKU values are between 5-8 alpha numeric characters'
)
RETURNS TABLE(
  inventory_id BIGINT COMMENT 'Unique identifier for each inventory record'
  ,sku STRING COMMENT 'Stock Keeping Unit - unique internal product identifier code'
  ,upc STRING COMMENT 'Universal Product Code - standardized barcode number for product identification'
  ,product_id BIGINT COMMENT 'Foreign key reference to the product table identifying the specific product'  
  ,store_id INT COMMENT 'Store identifier where inventory is located'
  ,store_quantity INT COMMENT 'Current available quantity of product in the specified store'
  ,warehouse STRING COMMENT 'Warehouse identifier where backup inventory is stored'
  ,warehouse_quantity INT COMMENT 'Current available quantity of product in the specified warehouse'
  ,retail_amount DOUBLE COMMENT 'Current retail price of the product'
  ,popularity_rating STRING COMMENT 'Rating indicating how popular/frequently purchased the product is (e.g., high, medium, low)'
  ,department STRING COMMENT 'Department within the store where the product is categorized'
  ,aisle_location STRING COMMENT 'Physical aisle location identifier where the product can be found in store'
  ,is_closeout BOOLEAN COMMENT 'Flag indicating whether the product is marked for closeout/clearance'
)
READS SQL DATA
COMMENT 'Retrieves detailed inventory information for products by SKU for a specific store. This function is designed for store-specific inventory management in retail applications.'
RETURN 
SELECT 
  inventory_id
  ,sku
  ,upc
  ,inventory.product_id
  ,store_id
  ,store_quantity
  ,warehouse
  ,warehouse_quantity
  ,retail_amount
  ,popularity_rating
  ,department
  ,aisle_location
  ,is_closeout
FROM {catalog_name}.{database_name}.inventory inventory
JOIN {catalog_name}.{database_name}.products products
ON inventory.product_id = products.product_id
WHERE ARRAY_CONTAINS(find_store_inventory_by_sku.sku, products.sku) 
  AND inventory.store_id = find_store_inventory_by_sku.store_id
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to retrieve store-specific inventory details by SKU"
    )

# Create the function
create_find_store_inventory_by_sku_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Store Inventory Lookup by SKU

# COMMAND ----------

# Test the find_store_inventory_by_sku function
test_df = execute_and_display_function(
    client=client,
    function_name=f"{catalog_name}.{database_name}.find_store_inventory_by_sku",
    parameters={"store_id": 101, "sku": ["DUN-KCP-001"]},
    description="Testing store-specific inventory lookup by SKU"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Store Inventory Lookup by UPC Function

# COMMAND ----------

def create_find_store_inventory_by_upc_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create the find_store_inventory_by_upc Unity Catalog function."""
    
    function_name = f"{catalog_name}.{database_name}.find_store_inventory_by_upc"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  store_id INT COMMENT 'The store identifier to retrieve inventory for'
  ,upc ARRAY<STRING> COMMENT 'One or more unique identifiers to retrieve. It may help to use another tool to provide this value. UPC values are between 10-16 alpha numeric characters'
)
RETURNS TABLE(
  inventory_id BIGINT COMMENT 'Unique identifier for each inventory record'
  ,sku STRING COMMENT 'Stock Keeping Unit - unique internal product identifier code'
  ,upc STRING COMMENT 'Universal Product Code - standardized barcode number for product identification'
  ,product_id BIGINT COMMENT 'Foreign key reference to the product table identifying the specific product'  
  ,store_id INT COMMENT 'Store identifier where inventory is located'
  ,store_quantity INT COMMENT 'Current available quantity of product in the specified store'
  ,warehouse STRING COMMENT 'Warehouse identifier where backup inventory is stored'
  ,warehouse_quantity INT COMMENT 'Current available quantity of product in the specified warehouse'
  ,retail_amount DOUBLE COMMENT 'Current retail price of the product'
  ,popularity_rating STRING COMMENT 'Rating indicating how popular/frequently purchased the product is (e.g., high, medium, low)'
  ,department STRING COMMENT 'Department within the store where the product is categorized'
  ,aisle_location STRING COMMENT 'Physical aisle location identifier where the product can be found in store'
  ,is_closeout BOOLEAN COMMENT 'Flag indicating whether the product is marked for closeout/clearance'
)
READS SQL DATA
COMMENT 'Retrieves detailed inventory information for products by UPC for a specific store. This function is designed for store-specific inventory management in retail applications.'
RETURN 
SELECT 
  inventory_id
  ,sku
  ,upc
  ,inventory.product_id
  ,store_id
  ,store_quantity
  ,warehouse
  ,warehouse_quantity
  ,retail_amount
  ,popularity_rating
  ,department
  ,aisle_location
  ,is_closeout
FROM {catalog_name}.{database_name}.inventory inventory
JOIN {catalog_name}.{database_name}.products products
ON inventory.product_id = products.product_id
WHERE ARRAY_CONTAINS(find_store_inventory_by_upc.upc, products.upc) 
  AND inventory.store_id = find_store_inventory_by_upc.store_id
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to retrieve store-specific inventory details by UPC"
    )

# Create the function
create_find_store_inventory_by_upc_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Store Inventory Lookup by UPC

# COMMAND ----------

# Test the find_store_inventory_by_upc function
test_df = execute_and_display_function(
    client=client,
    function_name=f"{catalog_name}.{database_name}.find_store_inventory_by_upc",
    parameters={"store_id": 101, "upc": ["234567890123"]},
    description="Testing store-specific inventory lookup by UPC"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Store Management Functions

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Store Lookup by Number Function

# COMMAND ----------

def create_find_store_by_number_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create the find_store_by_number Unity Catalog function using dim_store table."""
    
    function_name = f"{catalog_name}.{database_name}.find_store_by_number"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  store_ids ARRAY<INT> COMMENT 'One or more store identifiers to retrieve. Store IDs are integer values'
)
RETURNS TABLE(
  store_id INT COMMENT 'Unique identifier for each store in the system'
  ,store_name STRING COMMENT 'Display name of the store location'
  ,store_address STRING COMMENT 'Street address of the store location'
  ,store_city STRING COMMENT 'City where the store is located'
  ,store_state STRING COMMENT 'State or province where the store is located'
  ,store_zipcode STRING COMMENT 'Postal code for the store location'
  ,store_country STRING COMMENT 'Country where the store is located'
  ,store_phone STRING COMMENT 'Primary phone number for the store'
  ,store_email STRING COMMENT 'Email address for the store'
  ,store_manager_id STRING COMMENT 'Identifier for the store manager'
  ,opening_date DATE COMMENT 'Date when the store opened'
  ,store_area_sqft DOUBLE COMMENT 'Total floor space of the store in square feet'
  ,is_open_24_hours BOOLEAN COMMENT 'Flag indicating if the store is open 24 hours'
  ,latitude DOUBLE COMMENT 'Latitude coordinate of the store location'
  ,longitude DOUBLE COMMENT 'Longitude coordinate of the store location'
  ,region_id STRING COMMENT 'Identifier for the region the store belongs to'
  ,store_details_text STRING COMMENT 'Detailed text description of the store including location, hours, and services'
)
READS SQL DATA
COMMENT 'Retrieves detailed information about stores by their store IDs. This function is designed for store location and information retrieval in retail applications.'
RETURN 
SELECT 
  store_id
  ,store_name
  ,store_address
  ,store_city
  ,store_state
  ,store_zipcode
  ,store_country
  ,store_phone
  ,store_email
  ,store_manager_id
  ,opening_date
  ,store_area_sqft
  ,is_open_24_hours
  ,latitude
  ,longitude
  ,region_id
  ,store_details_text
FROM {catalog_name}.{database_name}.dim_stores 
WHERE ARRAY_CONTAINS(find_store_by_number.store_ids, dim_stores.store_id)
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to retrieve store details by store ID from dim_stores table"
    )

# Create the function
create_find_store_by_number_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Store Lookup by Number (Updated for dim_store)

# COMMAND ----------

# Test the find_store_by_number function with dim_store
try:
    print("🔍 Testing store lookup by store ID using dim_store table...")
    print("📋 Testing with store IDs: [1, 2]")
    
    test_df = execute_and_display_function(
        client=client,
        function_name=f"{catalog_name}.{database_name}.find_store_by_number",
        parameters={"store_ids": [1, 2]},
        description="Testing store lookup by store ID using dim_store table"
    )
    
    if test_df.empty:
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Verify that the dim_store table exists and has data:")
        print(f"   SELECT COUNT(*) FROM {catalog_name}.{database_name}.dim_stores;")
        print("2. Check if the store IDs exist in the table:")
        print(f"   SELECT store_id FROM {catalog_name}.{database_name}.dim_stores WHERE store_id IN (1, 2);")
        print("3. Ensure the data has been loaded from dim_stores_data.sql")
        print("4. Verify the function was created successfully")
    else:
        print(f"✅ Successfully retrieved {len(test_df)} store records!")
        
except Exception as e:
    print(f"❌ Test failed with error: {str(e)}")
    print("\n🔧 This might be due to:")
    print("- The dim_store table not existing")
    print("- The function not being created properly")
    print("- Database connection issues")
    print("- The data not being loaded yet")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Vector Search Store Location Functions

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Store Location Vector Search Function

# COMMAND ----------

def create_store_location_vector_search_tool(
    endpoint_name: str,
    index_name: str,
    columns: List[str],
    k: int = 10
) -> None:
    """
    Create a vector search tool for finding stores by location description.
    
    This function demonstrates how to use vector search for store location discovery
    based on natural language descriptions, store names, or geographic references.
    """
    
    def find_stores_by_location(content: str) -> Union[List[Document], List[Dict[str, Any]]]:
        """
        Find store details using semantic vector search based on location descriptions.

        This tool performs semantic search across the store directory to find locations that match
        the provided description, including store names, addresses, cities, or geographic references.
        It's particularly useful for natural language store discovery and location services.

        Args:
            content: Natural language description of the store location to search for

        Returns:
            List of Document objects containing matching store information, or empty list if packages unavailable
        """
        # Check if required imports are available
        if Document is None or DatabricksVectorSearch is None:
            logger.error("Required langchain_core or databricks_langchain packages not available")
            return []
            
        logger.info(f"Searching for stores with description: {content}")

        # Initialize the vector search client
        vector_search: VectorStore = DatabricksVectorSearch(
            endpoint=endpoint_name,
            index_name=index_name,
            columns=columns,
        )

        # Perform the semantic search
        results: List[Document] = vector_search.similarity_search(
            query=content, k=k
        )

        logger.info(f"Found {len(results)} store matches")
        return results
    
    return find_stores_by_location

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Vector Search Store Location Function

# COMMAND ----------

def test_store_vector_search() -> None:
    """Test the store vector search functionality."""
    
    # Check if required imports are available
    if Document is None or DatabricksVectorSearch is None:
        logger.warning("Skipping vector search test - required packages not available")
        print("Vector search functionality requires langchain_core and databricks_langchain packages")
        return
    
    # Load configuration to get vector store settings
    model_config_file = "../model_config.yaml"
    model_config = ModelConfig(development_config=model_config_file)
    
    # Get store vector store configuration
    vector_stores_config = model_config.get("resources").get("vector_stores")
    store_vector_store = vector_stores_config.get("store_vector_store")
    
    if not store_vector_store:
        logger.warning("Store vector store configuration not found")
        return
    
    endpoint_name = store_vector_store.get("endpoint_name")
    index_name = store_vector_store.get("index_name")
    columns = store_vector_store.get("columns", [])
    
    # Create the vector search tool
    search_tool = create_store_location_vector_search_tool(
        endpoint_name=endpoint_name,
        index_name=index_name,
        columns=columns,
        k=5
    )
    
    # Test queries
    test_queries = [
        "stores open 24 hours in San Francisco",
        "BrickMart locations in New York",
        "stores near downtown Los Angeles",
        "24 hour stores in California"
    ]
    
    for query in test_queries:
        try:
            logger.info(f"\n=== Testing query: {query} ===")
            results = search_tool(query)
            
            if results:
                logger.info(f"Found {len(results)} results:")
                for i, result in enumerate(results[:3], 1):
                    logger.info(f"  {i}. {result.page_content[:200]}...")
            else:
                logger.info("No results found")
                
        except Exception as e:
            logger.error(f"Error testing query '{query}': {str(e)}")

# Test the vector search functionality
try:
    test_store_vector_search()
except Exception as e:
    logger.error(f"Error in vector search test: {str(e)}")
    print("Vector search test failed - this is expected if langchain packages are not installed")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Enhanced Store Management Functions

# COMMAND ----------

def create_store_number_extraction_function(catalog_name: str, database_name: str, client: DatabricksFunctionClient) -> None:
    """Create a function to extract store numbers from text using SQL pattern matching."""
    
    function_name = f"{catalog_name}.{database_name}.extract_store_numbers"
    
    sql_function_body = f"""
CREATE OR REPLACE FUNCTION {function_name}(
  input_text STRING COMMENT 'Text input that may contain store numbers'
)
RETURNS ARRAY<STRING>
READS SQL DATA
COMMENT 'Extracts store numbers from natural language text using pattern matching. Store numbers are typically 3-4 digit numeric values.'
RETURN 
SELECT 
  COLLECT_LIST(DISTINCT store_id) as store_numbers
FROM {catalog_name}.{database_name}.dim_stores
WHERE input_text RLIKE CONCAT('\\\\b', store_id, '\\\\b')
"""
    
    create_function_safely(
        client=client,
        sql_function_body=sql_function_body,
        function_name=function_name,
        description="Function to extract store numbers from text using pattern matching"
    )

# Create the store number extraction function
create_store_number_extraction_function(catalog_name, database_name, client)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Test Store Number Extraction

# COMMAND ----------

# Test the extract_store_numbers function
test_df = execute_and_display_function(
    client=client,
    function_name=f"{catalog_name}.{database_name}.extract_store_numbers",
    parameters={"input_text": "I need help with store 001 and also check inventory at store 002"},
    description="Testing store number extraction from text"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Verify Table Existence and Data

# COMMAND ----------

def check_table_exists_and_data(catalog_name: str, database_name: str, table_name: str) -> None:
    """Check if a table exists and has data."""
    try:
        print(f"🔍 Checking table: {catalog_name}.{database_name}.{table_name}")
        
        # Try to query the table
        count_query = f"SELECT COUNT(*) as row_count FROM {catalog_name}.{database_name}.{table_name}"
        print(f"📊 Executing: {count_query}")
        
        # Note: This would need to be executed in a SQL cell or with proper SQL execution
        print("⚠️  Please run the following SQL query manually to check table status:")
        print(f"   {count_query}")
        print(f"   SELECT store_id, store_name FROM {catalog_name}.{database_name}.{table_name} LIMIT 5;")
        
    except Exception as e:
        print(f"❌ Error checking table: {str(e)}")

# Check if dim_store table exists and has data
check_table_exists_and_data(catalog_name, database_name, "dim_store")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC Successfully created and tested the following Unity Catalog functions:
# MAGIC
# MAGIC ### Product Functions:
# MAGIC - `find_product_by_sku` - Retrieve product details by SKU
# MAGIC - `find_product_by_upc` - Retrieve product details by UPC
# MAGIC
# MAGIC ### Inventory Functions:
# MAGIC - `find_inventory_by_sku` - Retrieve inventory across all stores by SKU
# MAGIC - `find_inventory_by_upc` - Retrieve inventory across all stores by UPC
# MAGIC - `find_store_inventory_by_sku` - Retrieve store-specific inventory by SKU
# MAGIC - `find_store_inventory_by_upc` - Retrieve store-specific inventory by UPC
# MAGIC
# MAGIC ### Store Functions:
# MAGIC - `find_store_by_number` - Retrieve store details by store ID (updated to use dim_store table)
# MAGIC - `extract_store_numbers` - Extract store numbers from natural language text using pattern matching
# MAGIC
# MAGIC ### Vector Search Functions:
# MAGIC - `find_stores_by_location` - Semantic search for stores using vector search based on location descriptions
# MAGIC - Store location vector search tool for natural language store discovery
# MAGIC
# MAGIC ### Key Updates:
# MAGIC 1. **Updated Store Table Reference**: All store functions now use `dim_store` table instead of `dim_stores`
# MAGIC 2. **Added Store Details Text**: Store functions now include `store_details_text` column for enhanced descriptions
# MAGIC 3. **Vector Search Integration**: Added vector search capabilities for semantic store location discovery
# MAGIC 4. **Store Number Extraction**: Added SQL-based pattern matching for extracting store numbers from text
# MAGIC 5. **Enhanced Testing**: Updated test cases to use correct store IDs from dim_store table
# MAGIC
# MAGIC These functions provide comprehensive foundation for the Retail AI system's product, inventory, and store management capabilities, with enhanced store location services through vector search.
