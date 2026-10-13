"""Print a serving endpoint's event timeline (UTC) since an optional HH:MM:SS cutoff.

Usage: python timeline.py <endpoint> [HH:MM:SS]
"""

import datetime
import re
import sys

from databricks.sdk import WorkspaceClient

endpoint: str = sys.argv[1]
since: str = sys.argv[2] if len(sys.argv) > 2 else "00:00:00"
w = WorkspaceClient()
events = w.api_client.do("GET", f"/api/2.0/serving-endpoints/{endpoint}/events")["events"]
for ev in sorted(events, key=lambda e: int(e["timestamp"])):
    ts = datetime.datetime.fromtimestamp(int(ev["timestamp"]) / 1000, datetime.UTC)
    if ts.strftime("%H:%M:%S") < since:
        continue
    msg = re.sub(r"retail_consumer_goods-hardware_store-", "", ev.get("message", ""))
    print(ts.strftime("%H:%M:%S"), ev.get("event_type", "")[:28].ljust(28), msg[:140])
