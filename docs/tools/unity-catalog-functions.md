# Unity Catalog Functions

Unity Catalog functions provide direct SQL-based access to product and inventory data. These functions are created and managed through the `04_unity_catalog_tools.py` notebook and offer high-performance database operations.

## Overview

The Unity Catalog functions are SQL functions that:
- Provide direct access to product and inventory tables
- Support batch operations with array parameters
- Return structured tabular data
- Integrate seamlessly with Databricks SQL Warehouse
- Offer the fastest query performance for exact matches

## Product Lookup Functions

### `find_product_by_sku`

Retrieves detailed product information by SKU identifiers.

**Function Signature:**
```sql
find_product_by_sku(sku ARRAY<STRING>) 
RETURNS TABLE(...)
```

**Parameters:**
- `sku`: Array of SKU identifiers (8-12 alphanumeric characters)

**Returns:**
- `product_id`: Unique identifier for each product
- `sku`: Stock Keeping Unit identifier
- `upc`: Universal Product Code
- `brand_name`: Manufacturer or brand name
- `product_name`: Display name for customers
- `short_description`: Brief product description
- `long_description`: Detailed product description
- `merchandise_class`: Broad category classification
- `class_cd`: Alphanumeric subcategory code
- `department_name`: Department classification
- `category_name`: Product category
- `subcategory_name`: Product subcategory
- `base_price`: Base retail price
- `msrp`: Manufacturer Suggested Retail Price

**Usage Example:**
```python
from databricks.sdk import WorkspaceClient
from unitycatalog.ai.core.databricks import DatabricksFunctionClient

client = DatabricksFunctionClient(client=WorkspaceClient())
result = client.execute_function(
    function_name="catalog.database.find_product_by_sku",
    parameters={"sku": ["STB-KCP-001", "DUN-KCP-001"]}
)
```

### `find_product_by_upc`

Retrieves detailed product information by UPC identifiers.

**Function Signature:**
```sql
find_product_by_upc(upc ARRAY<STRING>) 
RETURNS TABLE(...)
```

**Parameters:**
- `upc`: Array of UPC identifiers (10-16 alphanumeric characters)

**Returns:**
Same structure as `find_product_by_sku`

**Usage Example:**
```python
result = client.execute_function(
    function_name="catalog.database.find_product_by_upc",
    parameters={"upc": ["012345678901", "234567890123"]}
)
```

## Inventory Management Functions

### `find_inventory_by_sku`

Retrieves inventory information across all stores for specific SKUs.

**Function Signature:**
```sql
find_inventory_by_sku(sku ARRAY<STRING>) 
RETURNS TABLE(...)
```

**Parameters:**
- `sku`: Array of SKU identifiers (5-8 alphanumeric characters)

**Returns:**
- `inventory_id`: Unique inventory record identifier
- `sku`: Stock Keeping Unit identifier
- `upc`: Universal Product Code
- `product_id`: Foreign key to product table
- `store_id`: Store identifier
- `store_quantity`: Available quantity in store
- `warehouse`: Warehouse identifier
- `warehouse_quantity`: Available quantity in warehouse
- `retail_amount`: Current retail price
- `popularity_rating`: Product popularity (high/medium/low)
- `department`: Store department
- `aisle_location`: Physical aisle location
- `is_closeout`: Closeout/clearance flag

**Usage Example:**
```python
result = client.execute_function(
    function_name="catalog.database.find_inventory_by_sku",
    parameters={"sku": ["PET-KCP-001"]}
)
```

### `find_inventory_by_upc`

Retrieves inventory information across all stores for specific UPCs.

**Function Signature:**
```sql
find_inventory_by_upc(upc ARRAY<STRING>) 
RETURNS TABLE(...)
```

**Parameters:**
- `upc`: Array of UPC identifiers (10-16 alphanumeric characters)

**Returns:**
Same structure as `find_inventory_by_sku`

## Store-Specific Functions

### `find_store_inventory_by_sku`

Retrieves inventory information for a specific store and SKUs.

**Function Signature:**
```sql
find_store_inventory_by_sku(
    store_id INT,
    sku ARRAY<STRING>
) 
RETURNS TABLE(...)
```

**Parameters:**
- `store_id`: Store identifier
- `sku`: Array of SKU identifiers (5-8 alphanumeric characters)

**Returns:**
Same structure as `find_inventory_by_sku`

**Usage Example:**
```python
result = client.execute_function(
    function_name="catalog.database.find_store_inventory_by_sku",
    parameters={"store_id": 101, "sku": ["DUN-KCP-001"]}
)
```

### `find_store_inventory_by_upc`

Retrieves inventory information for a specific store and UPCs.

**Function Signature:**
```sql
find_store_inventory_by_upc(
    store_id INT,
    upc ARRAY<STRING>
) 
RETURNS TABLE(...)
```

**Parameters:**
- `store_id`: Store identifier
- `upc`: Array of UPC identifiers (10-16 alphanumeric characters)

**Returns:**
Same structure as `find_inventory_by_sku`

## Implementation Details

### Function Creation

Functions are created using the `create_uc_function` helper in the setup notebook:

```python
def create_uc_function(
    client: DatabricksFunctionClient,
    function_name: str,
    parameters: str,
    returns: str,
    comment: str,
    sql_body: str
) -> None:
    """Create a Unity Catalog function with error handling."""
    # Implementation details...
```

### Error Handling

All functions include robust error handling:

```python
def test_function(
    client: DatabricksFunctionClient,
    function_name: str,
    parameters: Dict[str, Any],
    display_results: bool = True
) -> pd.DataFrame:
    """Test a Unity Catalog function and return results as DataFrame."""
    try:
        result = client.execute_function(
            function_name=function_name,
            parameters=parameters
        )
        
        if result.error:
            raise Exception(f"Function execution error: {result.error}")
        
        return pd.read_csv(StringIO(result.value))
    except Exception as e:
        logger.error(f"Failed to execute function {function_name}: {str(e)}")
        raise
```

## Performance Characteristics

### Advantages
- **High Performance**: Direct SQL execution in Databricks SQL Warehouse
- **Batch Operations**: Support for multiple identifiers in single call
- **Structured Output**: Consistent tabular format
- **Type Safety**: Strong typing with SQL schema validation

### Best Practices
- **Batch Requests**: Use arrays to query multiple items at once
- **Appropriate Sizing**: Balance batch size with memory constraints
- **Error Handling**: Always check for execution errors
- **Result Processing**: Use pandas for data manipulation

## Configuration

Functions are configured in `model_config.yaml`:

```yaml
functions:
  find_product_by_sku:
    name: demos_genie.rcg_store_manager_gold.find_product_by_sku
  find_product_by_upc:
    name: demos_genie.rcg_store_manager_gold.find_product_by_upc
  find_inventory_by_sku:
    name: demos_genie.rcg_store_manager_gold.find_inventory_by_sku
  find_inventory_by_upc:
    name: demos_genie.rcg_store_manager_gold.find_inventory_by_upc
  find_store_inventory_by_sku:
    name: demos_genie.rcg_store_manager_gold.find_store_inventory_by_sku
  find_store_inventory_by_upc:
    name: demos_genie.rcg_store_manager_gold.find_store_inventory_by_upc
```

## Troubleshooting

### Common Issues

**Function not found**
```
Error: Function 'catalog.database.function_name' not found
Solution: Ensure functions are created via 04_unity_catalog_tools.py
```

**Permission denied**
```
Error: User does not have permission to execute function
Solution: Check Unity Catalog permissions in model_config.yaml
```

**Invalid parameters**
```
Error: Invalid parameter type or format
Solution: Verify parameter types match function signature
```

**Empty results**
```
Error: No results returned
Solution: Check if SKU/UPC values exist in the database
```

### Debugging Tips

1. **Test Individual Functions**: Use the test helpers in the setup notebook
2. **Check Logs**: Review Databricks SQL Warehouse logs
3. **Validate Data**: Ensure input identifiers are correctly formatted
4. **Monitor Performance**: Track execution times for optimization

## Integration with LangChain Tools

Unity Catalog functions can be wrapped as LangChain tools:

```python
from retail_ai.tools import create_uc_tools

# Create LangChain tools from UC functions
tools = create_uc_tools([
    "catalog.database.find_product_by_sku",
    "catalog.database.find_inventory_by_sku"
])

# Use in agent workflows
agent = create_agent(tools=tools)
```

## Next Steps

- [LangChain Tools](langchain-tools.md) - AI-powered tool wrappers
- [Vector Search](vector-search.md) - Semantic search capabilities
- [Developer Guide](../development/adding-tools.md) - Create custom functions
- [API Reference](../api/functions.md) - Complete function reference 