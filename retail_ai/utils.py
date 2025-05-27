import importlib
from typing import Any, Callable

from databricks.vector_search.client import VectorSearchClient


def callable_from_fqn(fqn: str) -> Callable[[Any, ...], Any]:
    """
    Dynamically import and return a callable function using its fully qualified name.

    This utility function allows dynamic loading of functions from their string
    representation, enabling configuration-driven function resolution at runtime.
    It's particularly useful for loading different components based on configuration
    without hardcoding import statements.

    Args:
        fqn: Fully qualified name of the function to import, in the format
             "module.submodule.function_name"

    Returns:
        The imported callable function

    Raises:
        ImportError: If the module cannot be imported
        AttributeError: If the function doesn't exist in the module
        TypeError: If the resolved object is not callable

    Example:
        >>> func = callable_from_fqn("retail_ai.models.get_latest_model_version")
        >>> version = func("my_model")
    """
    try:
        # Split the FQN into module path and function name
        module_path, func_name = fqn.rsplit(".", 1)

        # Dynamically import the module
        module = importlib.import_module(module_path)

        # Get the function from the module
        func = getattr(module, func_name)

        # Verify that the resolved object is callable
        if not callable(func):
            raise TypeError(f"Function {func_name} is not callable.")

        return func
    except (ImportError, AttributeError, TypeError) as e:
        # Provide a detailed error message that includes the original exception
        raise ImportError(f"Failed to import {fqn}: {e}")


# Vector Search Utility Functions

def endpoint_exists(vsc: VectorSearchClient, vs_endpoint_name: str) -> bool:
    """
    Check if a Vector Search endpoint exists in the Databricks workspace.

    This utility function verifies whether a given Vector Search endpoint is already
    provisioned, handling rate limit errors gracefully to avoid workflow disruptions.

    Args:
        vsc: Databricks Vector Search client instance
        vs_endpoint_name: Name of the Vector Search endpoint to check

    Returns:
        True if the endpoint exists, False otherwise

    Raises:
        Exception: If an unexpected error occurs while checking endpoint existence
                  (except for rate limit errors, which are handled gracefully)
    """
    try:
        # Retrieve all endpoints and check if the target endpoint name is in the list
        return vs_endpoint_name in [
            e["name"] for e in vsc.list_endpoints().get("endpoints", [])
        ]
    except Exception as e:
        # Special handling for rate limit errors to prevent workflow failures
        if "REQUEST_LIMIT_EXCEEDED" in str(e):
            print(
                "WARN: couldn't get endpoint status due to REQUEST_LIMIT_EXCEEDED error."
            )
            # Assume endpoint exists to avoid disrupting the workflow
            return True
        else:
            # Re-raise other unexpected errors
            raise e


def index_exists(
    vsc: VectorSearchClient, endpoint_name: str, index_full_name: str
) -> bool:
    """
    Check if a Vector Search index exists on a specific endpoint.

    This utility function verifies whether a given Vector Search index is already
    created on the specified endpoint, handling non-existence errors gracefully.

    Args:
        vsc: Databricks Vector Search client instance
        endpoint_name: Name of the Vector Search endpoint to check
        index_full_name: Fully qualified name of the index (catalog.schema.table)

    Returns:
        True if the index exists on the endpoint, False otherwise

    Raises:
        Exception: If an unexpected error occurs that isn't related to the index
                  not existing (e.g., permission issues)
    """
    try:
        # Attempt to describe the index - this will succeed only if the index exists
        vsc.get_index(endpoint_name, index_full_name).describe()
        return True
    except Exception as e:
        # Check if this is a "not exists" error or something else
        if "RESOURCE_DOES_NOT_EXIST" not in str(e):
            # For unexpected errors, provide a more helpful message
            print(
                "Unexpected error describing the index. This could be a permission issue."
            )
            raise e
    # If we reach here, the index doesn't exist
    return False
