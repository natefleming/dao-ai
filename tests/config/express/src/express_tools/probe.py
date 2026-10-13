"""Provenance probe for the express-deployment matrix, referenced as ``type: python``.

Ships through the colocated ``src/`` convention. Reports where it was loaded
from and which optional third-party libraries the serving environment can
import, so a single tool call proves custom code and ``app.pip_requirements``
both reached the endpoint.
"""

import importlib
import sys
from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_core.tools import tool as create_tool

# Libraries the ``express_full`` config adds via ``app.pip_requirements``: one
# pure-python, one with native extensions.
_PROBED_LIBS: tuple[str, ...] = ("humanize", "rapidfuzz")


@create_tool
def environment_probe() -> str:
    """Report this tool's module path, the Python version, and the versions of
    the probed third-party libraries. Call this whenever the user asks for an
    environment probe or provenance report.

    Returns:
        A one-line provenance report.
    """
    libs: list[str] = []
    for name in _PROBED_LIBS:
        try:
            module = importlib.import_module(name)
            libs.append(f"{name}={getattr(module, '__version__', 'unknown')}")
        except ImportError:
            libs.append(f"{name}=MISSING")

    return (
        f"module={Path(__file__).resolve()} "
        f"python={sys.version.split()[0]} "
        f"libs=[{', '.join(libs)}]"
    )


environment_probe_tool: BaseTool = environment_probe
