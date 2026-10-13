"""Validate, from MLflow traces, that pip libraries and custom code ran during inference.

For each ``endpoint=experiment_id`` argument: send one inference request, wait for
its trace, then check the ``fuzzy_product_lookup`` TOOL span. That tool uses
rapidfuzz and humanize, and its output must match values computed here
independently: the fuzz.ratio score from a stdlib LCS, and the sales figures
formatted by hand. The ``environment_probe`` and ``greet`` spans are reported
alongside. The trace, not the LLM's reply, is the source of truth.

Usage: python validate_traces.py <endpoint>=<experiment_id> ...
"""

import json
import sys
import time

import mlflow
import requests
from databricks.sdk import WorkspaceClient

QUERY: str = "cordles hamer dril"
CATALOG: dict[str, tuple[int, int]] = {
    "Cordless Hammer Drill": (12999, 1250000),
    "Exterior Wood Screws": (899, 87000),
    "Interior Latex Paint": (3499, 432100),
}


def _lcs(a: str, b: str) -> int:
    prev: list[int] = [0] * (len(b) + 1)
    for ca in a:
        cur: list[int] = [0]
        for j, cb in enumerate(b):
            cur.append(prev[j] + 1 if ca == cb else max(prev[j + 1], cur[-1]))
        prev = cur
    return prev[-1]


def expected_output(query: str) -> str:
    """The tool's output minus its version suffix, computed without the libraries."""
    scores = {n: 200 * _lcs(query, n) / (len(query) + len(n)) for n in CATALOG}
    name: str = max(scores, key=scores.get)
    price, units = CATALOG[name]
    return (
        f"best={name} score={scores[name]:.2f} price=${price / 100:.2f} "
        f"units_sold={units:,} ({units / 1e6:.1f} million)"
    )


def run(endpoint: str, experiment_id: str, w: WorkspaceClient) -> bool:
    started_ms: int = int(time.time() * 1000)
    prompt: str = (
        f"Look up the product '{QUERY}' with fuzzy_product_lookup, then call "
        "environment_probe and greet (name Nate)."
    )
    headers = {**w.config.authenticate(), "Content-Type": "application/json"}
    for _ in range(40):  # scale-from-zero can take a few minutes
        try:
            r = requests.post(
                f"{w.config.host}/serving-endpoints/{endpoint}/invocations",
                headers=headers,
                json={"input": [{"role": "user", "content": prompt}]},
                timeout=300,
            )
            if r.status_code == 200:
                break
        except requests.RequestException:
            pass
        time.sleep(15)
    else:
        print(f"[{endpoint}] FAIL: no 200 response")
        return False

    for _ in range(40):  # traces are exported asynchronously
        traces = mlflow.search_traces(
            experiment_ids=[experiment_id],
            filter_string=f"timestamp_ms > {started_ms}",
            return_type="list",
        )
        if traces:
            break
        time.sleep(15)
    else:
        print(f"[{endpoint}] FAIL: no trace in experiment {experiment_id}")
        return False

    trace = traces[0]
    tools = {s.name: s for s in trace.data.spans if (s.span_type or "") == "TOOL"}
    print(f"[{endpoint}] trace {trace.info.trace_id} TOOL spans: {sorted(tools)}")
    for name in ("environment_probe", "greet"):
        if name in tools:
            print(f"  {name}: {tools[name].outputs.get('content')}")

    span = tools.get("fuzzy_product_lookup")
    if span is None:
        print(f"[{endpoint}] FAIL: fuzzy_product_lookup did not run")
        return False
    actual: str = span.outputs.get("content", "")
    expected: str = expected_output(json.loads(json.dumps(span.inputs))["query"])
    ok: bool = actual.startswith(expected) and span.status.status_code.name == "OK"
    print(f"  fuzzy_product_lookup input:  {span.inputs}")
    print(f"  fuzzy_product_lookup output: {actual}")
    print(f"  expected prefix:             {expected}")
    print(f"[{endpoint}] {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    mlflow.set_tracking_uri("databricks")
    client = WorkspaceClient()
    results = [run(*arg.split("=", 1), client) for arg in sys.argv[1:]]
    sys.exit(0 if all(results) else 1)
