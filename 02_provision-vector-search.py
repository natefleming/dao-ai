# Databricks notebook source
# COMMAND ----------

from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())

# COMMAND ----------

from dotenv import find_dotenv, load_dotenv
from typing import Any, Sequence, List, Dict
from mlflow.models import ModelConfig
from databricks.vector_search.client import VectorSearchClient
from databricks.vector_search.index import VectorSearchIndex
from retail_ai.utils import endpoint_exists, index_exists

_ = load_dotenv(find_dotenv())

# COMMAND ----------

def provision_vector_store_index(vsc: VectorSearchClient, vector_store_config: Dict[str, Any]) -> None:
    """Provision a single vector store index based on configuration."""
    
    embedding_model_endpoint_name: str = vector_store_config.get("embedding_model_endpoint_name")
    endpoint_name: str = vector_store_config.get("endpoint_name")
    endpoint_type: str = vector_store_config.get("endpoint_type")
    index_name: str = vector_store_config.get("index_name")
    source_table_name: str = vector_store_config.get("source_table_name")
    primary_key: str = vector_store_config.get("primary_key")
    embedding_source_column: str = vector_store_config.get("embedding_source_column")
    columns: Sequence[str] = vector_store_config.get("columns", [])

    print(f"\n=== Provisioning Vector Store Index ===")
    print(f"embedding_model_endpoint_name: {embedding_model_endpoint_name}")
    print(f"endpoint_name: {endpoint_name}")
    print(f"endpoint_type: {endpoint_type}")
    print(f"index_name: {index_name}")
    print(f"source_table_name: {source_table_name}")
    print(f"primary_key: {primary_key}")
    print(f"embedding_source_column: {embedding_source_column}")
    print(f"columns: {columns}")

    # Ensure endpoint exists
    if not endpoint_exists(vsc, endpoint_name):
        print(f"Creating endpoint {endpoint_name}...")
        vsc.create_endpoint_and_wait(name=endpoint_name, verbose=True, endpoint_type=endpoint_type)
    
    print(f"Endpoint named {endpoint_name} is ready.")

    # Create or sync index
    if not index_exists(vsc, endpoint_name, index_name):
        print(f"Creating index {index_name} on endpoint {endpoint_name}...")
        vsc.create_delta_sync_index_and_wait(
            endpoint_name=endpoint_name,
            index_name=index_name,
            source_table_name=source_table_name,
            pipeline_type="TRIGGERED",
            primary_key=primary_key,
            embedding_source_column=embedding_source_column, 
            embedding_model_endpoint_name=embedding_model_endpoint_name
        )
    else:
        print(f"Index {index_name} already exists. Syncing...")
        vsc.get_index(endpoint_name, index_name).sync()

    print(f"Index {index_name} on table {source_table_name} is ready")

# COMMAND ----------

def provision_all_vector_stores() -> None:
    """Provision all vector store indexes defined in the configuration."""
    
    model_config_file: str = "model_config.yaml"
    config: ModelConfig = ModelConfig(development_config=model_config_file)
    
    # Get list of vector stores to provision
    vector_stores_config = config.get("resources").get("vector_stores")
    indexes_to_provision: List[Dict[str, Any]] = vector_stores_config.get("indexes_to_provision", [])
    
    if not indexes_to_provision:
        print("No vector store indexes configured for provisioning.")
        return
    
    print(f"Found {len(indexes_to_provision)} vector store indexes to provision:")
    for i, vs_config in enumerate(indexes_to_provision, 1):
        print(f"  {i}. {vs_config.get('index_name')}")
    
    # Initialize vector search client
    vsc: VectorSearchClient = VectorSearchClient()
    
    # Provision each vector store index
    for vs_config in indexes_to_provision:
        try:
            provision_vector_store_index(vsc, vs_config)
        except Exception as e:
            print(f"Error provisioning index {vs_config.get('index_name')}: {str(e)}")
            raise

# COMMAND ----------

# Provision all vector stores
provision_all_vector_stores()

# COMMAND ----------

def test_vector_search() -> None:
    """Test vector search functionality for all provisioned indexes."""
    
    model_config_file: str = "model_config.yaml"
    config: ModelConfig = ModelConfig(development_config=model_config_file)
    
    vector_stores_config = config.get("resources").get("vector_stores")
    indexes_to_provision: List[Dict[str, Any]] = vector_stores_config.get("indexes_to_provision", [])
    
    vsc: VectorSearchClient = VectorSearchClient()
    
    # Test queries for different index types
    test_queries = {
        "product": "What is the best hammer for drywall?",
        "store": "What stores are open 24 hours in San Francisco?"
    }
    
    for vs_config in indexes_to_provision:
        index_name = vs_config.get("index_name")
        endpoint_name = vs_config.get("endpoint_name")
        columns = vs_config.get("columns", [])
        
        print(f"\n=== Testing Vector Search for {index_name} ===")
        
        # Determine query type based on index name
        if "product" in index_name.lower():
            query = test_queries["product"]
        elif "store" in index_name.lower():
            query = test_queries["store"]
        else:
            query = "test query"
        
        try:
            index: VectorSearchIndex = vsc.get_index(endpoint_name, index_name)
            k: int = 3
            
            search_results: Dict[str, Any] = index.similarity_search(
                query_text=query,
                columns=columns,
                num_results=k
            )
            
            chunks: List[str] = search_results.get('result', {}).get('data_array', [])
            
            print(f"Query: {query}")
            print(f"Results found: {len(chunks)}")
            if chunks:
                print("Sample results:")
                for i, chunk in enumerate(chunks[:2], 1):
                    print(f"  {i}. {str(chunk)[:200]}...")
            
        except Exception as e:
            print(f"Error testing index {index_name}: {str(e)}")

# COMMAND ----------

# Test vector search functionality
test_vector_search()
