"""A tool factory for the express-deployment matrix, referenced as ``type: factory``.

Ships through ``app.code_paths``, so a working tool proves an explicitly declared
code path (and the YAML ``args:``) reached the endpoint.
"""

from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_core.tools import tool as create_tool


def create_greeting_tool(salutation: str) -> BaseTool:
    """Create a tool that greets a person with the configured salutation.

    Args:
        salutation: Word placed before the name, e.g. ``"Ahoy"``.

    Returns:
        A LangChain tool that returns the greeting plus this module's path.
    """

    @create_tool
    def greet(name: str) -> str:
        """Greet a person by name. Use whenever the user asks to be greeted.

        Args:
            name: The person's name.

        Returns:
            The greeting and the path this tool's module was loaded from.
        """
        return f"{salutation}, {name}! [loaded from {Path(__file__).resolve()}]"

    return greet
