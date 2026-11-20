"""Measure catalog operations with synthetic metadata (not full bundle imports)."""
import json
import platform
import tempfile
import time
import tracemalloc
from pathlib import Path

from skill_library.core import write_records
from skill_library.operations import rebuild_indexes, search


def run(count):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        records = [{"id": f"{i:020d}", "name": f"skill-{i}",
                    "description": "React accessibility workflow", "path": f"Category-{i % 10}/skill-{i}"}
                   for i in range(count)]
        write_records(root, records)
        tracemalloc.start()
        start = time.perf_counter()
        rebuild_indexes(root, records)
        index_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        matches = search(root, "react accessibility")
        search_ms = (time.perf_counter() - start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {"skills": count, "index_ms": round(index_ms, 2),
                "search_ms": round(search_ms, 2), "peak_mib": round(peak / 2**20, 2),
                "matches": len(matches)}


if __name__ == "__main__":
    print(json.dumps({"platform": platform.platform(), "python": platform.python_version(),
                      "results": [run(n) for n in (0, 1, 100, 1000, 10000)]}, indent=2))
