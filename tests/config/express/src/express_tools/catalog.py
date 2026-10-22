"""Fuzzy product lookup for the express-deployment matrix, referenced as ``type: python``.

Exercises the ``app.pip_requirements`` libraries during inference rather than
merely importing them: ``rapidfuzz`` ranks the LLM-supplied query against a fixed
catalog and ``humanize`` formats the result. Every value is deterministic, so a
trace's tool-span output can be checked exactly against a stdlib recomputation.
"""

import humanize
import rapidfuzz
from langchain_core.tools import BaseTool
from langchain_core.tools import tool as create_tool
from rapidfuzz import fuzz, process

# name -> (price in cents, units sold)
_CATALOG: dict[str, tuple[int, int]] = {
    "Cordless Hammer Drill": (12999, 1250000),
    "Exterior Wood Screws": (899, 87000),
    "Interior Latex Paint": (3499, 432100),
}


@create_tool
def fuzzy_product_lookup(query: str) -> str:
    """Find the catalog product that best matches a possibly misspelled name.

    Use this whenever the user asks to look up a product by name.

    Args:
        query: The product name exactly as the user wrote it, typos included.

    Returns:
        The best match, its similarity score, and its formatted sales figures.
    """
    name, score, _ = process.extractOne(query, list(_CATALOG), scorer=fuzz.ratio)
    price_cents, units = _CATALOG[name]
    return (
        f"best={name} score={score:.2f} "
        f"price=${price_cents / 100:.2f} "
        f"units_sold={humanize.intcomma(units)} ({humanize.intword(units)}) "
        f"[rapidfuzz={rapidfuzz.__version__} humanize={humanize.__version__}]"
    )


fuzzy_product_lookup_tool: BaseTool = fuzzy_product_lookup
