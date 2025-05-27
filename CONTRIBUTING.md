# Contributing to Retail AI Agent

This guide helps developers understand the tools architecture and contribute effectively to the Retail AI Agent project.

## Tools Architecture & Patterns

### Tool Design Philosophy

The `retail_ai/tools.py` module follows a **factory pattern** approach where functions create specialized tools that can be used by LangChain agents. This design provides:

- **Modularity**: Each tool is self-contained and reusable
- **Type Safety**: Pydantic models ensure data consistency
- **Observability**: MLflow tracing and logging throughout
- **Databricks Native**: Leverages the full Databricks platform

### Tool Categories

#### 1. LLM-Powered Analysis Tools

These tools use language models with structured output to perform complex analysis:

```python
def create_product_comparison_tool(llm: LanguageModelLike) -> Callable:
    @tool
    def product_comparison(products: list[dict]) -> ComparisonResult:
        llm_with_tools = llm.with_structured_output(ComparisonResult)
        return llm_with_tools.invoke(formatted_prompt)
    return product_comparison
```

**Pattern**: 
- Define Pydantic models for structured output
- Create prompt templates for consistent results
- Use `llm.with_structured_output()` for type-safe responses

**Examples**:
- `create_product_comparison_tool()`: Compare multiple products
- `create_product_classification_tool()`: Classify products into categories
- `create_sku_extraction_tool()`: Extract SKU codes from text

#### 2. Database Query Tools

These tools execute SQL queries against Databricks warehouses:

```python
def create_find_product_by_sku_tool(warehouse_id: str):
    @tool
    def find_product_by_sku(skus: list[str]) -> tuple:
        w = WorkspaceClient()
        statement = f"SELECT * FROM catalog.schema.function(ARRAY({skus}))"
        response = w.statement_execution.execute_statement(statement, warehouse_id)
        # Handle async execution with polling
        return response.result.data_array
    return find_product_by_sku
```

**Pattern**:
- Use `WorkspaceClient()` for Databricks API access
- Execute SQL statements with proper error handling
- Poll for completion on long-running queries
- Return structured data from Unity Catalog functions

**Examples**:
- `create_find_product_by_sku_tool()`: Look up products by SKU
- `create_find_inventory_by_sku_tool()`: Check inventory levels
- `create_find_store_inventory_by_sku_tool()`: Store-specific queries

#### 3. Vector Search Tools

These tools perform semantic search using Databricks Vector Search:

```python
def find_product_details_by_description_tool(endpoint_name, index_name, columns):
    @tool
    @mlflow.trace(span_type="RETRIEVER", name="vector_search")
    def find_product_details_by_description(content: str):
        vector_search = DatabricksVectorSearch(
            endpoint=endpoint_name,
            index_name=index_name,
            columns=columns
        )
        return vector_search.similarity_search(query=content, k=k)
    return find_product_details_by_description
```

**Pattern**:
- Use `@mlflow.trace()` for observability
- Initialize `DatabricksVectorSearch` with endpoint/index
- Return `Document` objects with metadata
- Register retriever schema with MLflow

#### 4. Unity Catalog Integration Tools

These tools automatically wrap UC functions as LangChain tools:

```python
def create_uc_tools(function_names: str | Sequence[str]) -> Sequence[BaseTool]:
    client = DatabricksFunctionClient()
    toolkit = UCFunctionToolkit(function_names=function_names, client=client)
    return toolkit.tools
```

**Pattern**:
- Use `UCFunctionToolkit` for automatic wrapping
- Support single function or list of functions
- Functions become callable tools with proper schemas

#### 5. External Service Tools

These tools integrate with external services:

```python
def create_genie_tool(space_id: Optional[str] = None):
    genie = Genie(space_id=space_id)
    
    @tool
    def genie_tool(question: str) -> GenieResponse:
        return genie.ask_question(question)
    return genie_tool
```

**Examples**:
- `create_genie_tool()`: Natural language to SQL via Databricks Genie
- `search_tool()`: Web search using DuckDuckGo

### Data Models

The tools use Pydantic models for structured data:

```python
class ProductInfo(BaseModel):
    product_id: str = Field(description="Unique identifier")
    product_name: str = Field(description="Name of the product")
    attributes: list[ProductAttribute] = Field(description="Product attributes")
    overall_rating: int = Field(description="Rating 1-10")
    
    model_config = {
        "extra": "forbid",  # Prevent additional properties
        "json_schema_extra": {"additionalProperties": False}
    }
```

**Key Features**:
- Strict validation with `"extra": "forbid"`
- Detailed field descriptions for LLM understanding
- Nested models for complex data structures
- JSON schema generation for API documentation

## Development Workflow

### Project Structure

```
retail_ai/
├── agents.py          # Agent implementations
├── catalog.py         # Unity Catalog integration
├── graph.py           # LangGraph workflow definition
├── models.py          # MLflow model integration
├── nodes.py           # Agent node definitions
├── tools.py           # Tool definitions (main focus)
└── vector_search.py   # Vector search utilities

notebooks/
├── 05_agent_as_code_driver.py    # Model logging & registration
├── 06_evaluate_agent.py          # Model evaluation
└── 07_deploy_agent.py            # Model deployment & permissions
```

### Notebook Workflow

The development workflow is organized into focused notebooks:

1. **`05_agent_as_code_driver.py`**: 
   - Model development and logging
   - Automatic model registration
   - Direct model testing

2. **`06_evaluate_agent.py`**: 
   - Formal MLflow evaluation
   - Evaluation data loading
   - Performance metrics

3. **`07_deploy_agent.py`**: 
   - Model alias management (Champion)
   - Endpoint deployment
   - Permissions configuration

## Adding New Tools

To add a new tool, follow these patterns:

### 1. Define Data Models (if needed)

```python
class YourDataModel(BaseModel):
    field_name: str = Field(description="Clear description")
    
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"additionalProperties": False}
    }
```

### 2. Create Tool Factory Function

```python
def create_your_tool(required_params) -> Callable:
    """
    Create a tool that does something specific.
    
    Args:
        required_params: Description of parameters
        
    Returns:
        A callable tool function
    """
    
    @tool
    def your_tool(input_param: str) -> YourDataModel:
        """
        Tool description that the agent will see.
        
        Args:
            input_param: Description of what this parameter does
            
        Returns:
            Structured result following YourDataModel schema
        """
        logger.debug(f"your_tool: input={input_param}")
        
        # Tool implementation here
        result = process_input(input_param)
        
        logger.debug(f"your_tool: result={result}")
        return result
    
    return your_tool
```

### 3. Add MLflow Tracing (for retrieval tools)

```python
@tool
@mlflow.trace(span_type="RETRIEVER", name="your_tool_name")
def your_retrieval_tool(query: str) -> Sequence[Document]:
    # Implementation
    pass
```

### 4. Register with Agent

Add your tool to the appropriate agent in `retail_ai/graph.py`:

```python
# In the agent creation function
your_tool = create_your_tool(config_params)
tools = [existing_tools..., your_tool]
```

## Testing Tools

### Unit Testing

```python
def test_your_tool():
    tool = create_your_tool(test_params)
    result = tool.invoke("test input")
    assert isinstance(result, YourDataModel)
    assert result.field_name == "expected_value"
```

### Integration Testing

Test tools in the context of the full agent:

```python
# Use the evaluation notebook
example_input = {"messages": [{"role": "user", "content": "test your tool"}]}
result = app.invoke(example_input)
```

## Best Practices

### 1. Error Handling

```python
@tool
def robust_tool(input_param: str) -> ResultModel:
    try:
        result = external_service.call(input_param)
        if not result:
            logger.warning(f"No results for input: {input_param}")
            return ResultModel(status="no_results")
        return ResultModel(data=result)
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        raise
```

### 2. Logging

```python
from loguru import logger

@tool
def well_logged_tool(input_param: str):
    logger.debug(f"tool_name: input={input_param}")
    
    # Log important intermediate steps
    processed = process_input(input_param)
    logger.debug(f"tool_name: processed={processed}")
    
    result = generate_result(processed)
    logger.debug(f"tool_name: result={result}")
    return result
```

### 3. Configuration

Use the model config for tool parameters:

```python
def create_configurable_tool(model_config: ModelConfig):
    endpoint = model_config.get("resources").get("endpoints").get("your_endpoint")
    
    @tool
    def configurable_tool(input_param: str):
        # Use endpoint from config
        pass
    return configurable_tool
```

### 4. Documentation

- Write clear docstrings that agents can understand
- Include parameter descriptions and examples
- Document return value structure
- Add type hints for all parameters

## Code Quality

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run checks
pre-commit run --all-files
```

### Type Checking

```bash
# Run mypy for type checking
mypy retail_ai/
```

### Testing

```bash
# Run tests
pytest tests/
```

## Tool Implementation Examples

### Example 1: Simple LLM Tool

```python
def create_sentiment_analysis_tool(llm: LanguageModelLike) -> Callable:
    """Create a tool that analyzes customer sentiment."""
    
    class SentimentResult(BaseModel):
        sentiment: Literal["positive", "negative", "neutral"] = Field(
            description="Overall sentiment of the text"
        )
        confidence: float = Field(
            description="Confidence score between 0 and 1"
        )
        reasoning: str = Field(
            description="Brief explanation of the sentiment analysis"
        )
        
        model_config = {
            "extra": "forbid",
            "json_schema_extra": {"additionalProperties": False}
        }
    
    @tool
    def sentiment_analysis(text: str) -> SentimentResult:
        """
        Analyze the sentiment of customer feedback or reviews.
        
        Args:
            text: The text to analyze for sentiment
            
        Returns:
            SentimentResult with sentiment, confidence, and reasoning
        """
        logger.debug(f"sentiment_analysis: text={text[:100]}...")
        
        prompt = f"Analyze the sentiment of this text: {text}"
        llm_with_tools = llm.with_structured_output(SentimentResult)
        result = llm_with_tools.invoke(prompt)
        
        logger.debug(f"sentiment_analysis: result={result}")
        return result
    
    return sentiment_analysis
```

### Example 2: Database Query Tool

```python
def create_price_lookup_tool(warehouse_id: str) -> Callable:
    """Create a tool that looks up current product prices."""
    
    @tool
    def price_lookup(product_ids: list[str]) -> list[dict]:
        """
        Look up current prices for one or more products.
        
        Args:
            product_ids: List of product IDs to look up prices for
            
        Returns:
            List of dictionaries with product_id, current_price, and currency
        """
        logger.debug(f"price_lookup: product_ids={product_ids}")
        
        w = WorkspaceClient()
        
        # Format product IDs for SQL
        ids_str = ",".join([f"'{pid}'" for pid in product_ids])
        statement = f"""
            SELECT product_id, current_price, currency 
            FROM catalog.schema.product_prices 
            WHERE product_id IN ({ids_str})
        """
        
        logger.debug(f"price_lookup: executing SQL: {statement}")
        
        response = w.statement_execution.execute_statement(
            statement=statement, 
            warehouse_id=warehouse_id
        )
        
        # Poll for completion
        while response.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            response = w.statement_execution.get_statement(response.statement_id)
        
        result = response.result.data_array if response.result else []
        logger.debug(f"price_lookup: result={result}")
        
        return result
    
    return price_lookup
```

### Example 3: Vector Search Tool

```python
def create_similar_products_tool(endpoint_name: str, index_name: str) -> Callable:
    """Create a tool that finds similar products using vector search."""
    
    @tool
    @mlflow.trace(span_type="RETRIEVER", name="similar_products_search")
    def find_similar_products(product_description: str, limit: int = 5) -> list[dict]:
        """
        Find products similar to the given description.
        
        Args:
            product_description: Description of the product to find similar items for
            limit: Maximum number of similar products to return
            
        Returns:
            List of similar products with metadata
        """
        logger.debug(f"find_similar_products: description={product_description}")
        
        vector_search = DatabricksVectorSearch(
            endpoint=endpoint_name,
            index_name=index_name,
            columns=["product_id", "name", "description", "category", "price"]
        )
        
        documents = vector_search.similarity_search(
            query=product_description, 
            k=limit
        )
        
        # Convert documents to structured format
        results = []
        for doc in documents:
            results.append({
                "product_id": doc.metadata.get("product_id"),
                "name": doc.metadata.get("name"),
                "description": doc.page_content,
                "category": doc.metadata.get("category"),
                "price": doc.metadata.get("price"),
                "similarity_score": doc.metadata.get("score", 0.0)
            })
        
        logger.debug(f"find_similar_products: found {len(results)} similar products")
        return results
    
    return find_similar_products
```

## Troubleshooting

### Common Issues

1. **Tool Not Found**: Ensure tool is registered in the agent configuration
2. **Type Errors**: Check Pydantic model definitions and field types
3. **Database Errors**: Verify Unity Catalog permissions and function names
4. **Vector Search Issues**: Check endpoint status and index configuration

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("retail_ai").setLevel(logging.DEBUG)
```

Use MLflow tracing to debug tool execution:

```python
# View traces in MLflow UI
mlflow.set_tracking_uri("databricks")
```

### Performance Tips

1. **Batch Operations**: Group multiple queries when possible
2. **Caching**: Cache expensive operations using `@lru_cache`
3. **Async Operations**: Use async patterns for I/O-bound operations
4. **Resource Management**: Properly close database connections and clients

## Contributing Guidelines

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Add tests** for any new tools or functionality
3. **Update documentation** including docstrings and examples
4. **Run quality checks** (linting, type checking, tests)
5. **Submit pull request** with clear description of changes

### Code Review Checklist

- [ ] Tool follows established patterns
- [ ] Proper error handling and logging
- [ ] Type hints and Pydantic models
- [ ] Clear documentation and examples
- [ ] Tests cover new functionality
- [ ] MLflow tracing for retrieval tools
- [ ] Configuration uses model config

### Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Documentation**: Check existing docs and code examples
- **Community**: Join the project community channels

This contributing guide provides the foundation for building robust, maintainable tools that integrate seamlessly with the Retail AI Agent architecture. 