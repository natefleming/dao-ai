"""
External Tools

This module contains tool creation functions for external services including
Databricks Genie for SQL generation and web search capabilities.
"""

from typing import Callable, Optional

from databricks_ai_bridge.genie import GenieResponse
from databricks_langchain.genie import Genie
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool, tool
from loguru import logger
from mlflow.models import ModelConfig


def create_genie_tool(space_id: Optional[str] = None) -> Callable[[str], GenieResponse]:
    """
    Create a tool that uses Databricks Genie for SQL generation and data analysis.

    Genie is Databricks' AI-powered SQL assistant that can generate SQL queries
    from natural language descriptions and provide data insights.

    Args:
        space_id: Optional Databricks space ID for Genie context

    Returns:
        A callable tool function that generates SQL and provides data analysis
    """
    logger.debug("create_genie_tool")

    @tool
    def genie_tool(question: str) -> GenieResponse:
        """
        Generate SQL queries and provide data analysis using Databricks Genie.

        This tool leverages Databricks Genie to convert natural language questions
        into SQL queries and execute them against your data warehouse, providing
        both the generated SQL and the results.

        Args:
            question: Natural language question about your data

        Returns:
            GenieResponse containing the generated SQL query and results
        """
        logger.debug(f"genie_tool: {question}")

        # Initialize Genie client
        genie = Genie(space_id=space_id)
        
        # Generate SQL and execute query
        response = genie.ask(question)
        
        logger.debug(f"Genie response: {response}")
        return response

    return genie_tool


def search_tool(model_config: ModelConfig) -> BaseTool:
    """
    Create a web search tool using DuckDuckGo for external information retrieval.

    This tool enables agents to search the web for current information, product reviews,
    DIY tutorials, or any information not available in the internal knowledge base.

    Args:
        model_config: Model configuration containing search settings

    Returns:
        A BaseTool instance for web search functionality
    """
    logger.debug("search_tool")
    
    # Create DuckDuckGo search tool
    search = DuckDuckGoSearchRun()
    
    # Customize the tool description for retail context
    search.description = """
    Search the web for current information, product reviews, tutorials, or any information 
    not available in the internal retail database. Useful for:
    - Current product reviews and ratings
    - DIY project instructions and tutorials  
    - Product availability at other retailers
    - General information about products or brands
    - Current news or trends related to products
    
    Input should be a search query string.
    """
    
    return search 