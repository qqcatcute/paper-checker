"""Reproducible synthetic workload; timing, memory, and profiling run separately."""

import argparse
import cProfile
import hashlib
import io
import json
import platform
import pstats
import random
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

from checker.similarity import similarity

PROJECT = Path(__file__).resolve().parents[1]


def make_workload(size: int = 120000) -> tuple[str, str]:
    """Build diverse Chinese input with deletions, replacements, and additions."""
    rng = random.Random(3224004157)
    alphabet = [chr(0x4E00 + index) for index in range(2000)]
    original = "".join(rng.choices(alphabet, k=size))
    changed = list(original)
    for index in range(0, len(changed), 17):
        changed[index] = rng.choice(alphabet)
    candidate = "".join(changed[size // 20 :]) + "".join(rng.choices(alphabet, k=size // 10))
    return original, candidate


def run(label: str, output: Path, size: int, repeats: int) -> dict:
    """Measure the same workload using independent instrumentation passes."""
    output.mkdir(parents=True, exist_ok=True)
    original, candidate = make_workload(size)
    expected = similarity(original, candidate)  # Warm up before timing.
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        actual = similarity(original, candidate)
        timings.append(time.perf_counter() - start)
        if abs(actual - expected) > 1e-12:
            raise RuntimeError("Repeated runs produced different scores")

    tracemalloc.start()
    similarity(original, candidate)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    profiler = cProfile.Profile()
    profiler.runcall(similarity, original, candidate)
    profiler.dump_stats(str(output / f"{label}.prof"))
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs().sort_stats("cumulative").print_stats(25)
    stats.sort_stats("tottime").print_stats(25)
    (output / f"{label}-profile.txt").write_text(stream.getvalue(), encoding="utf-8")
    functions = []
    for (filename, line, name), (primitive, calls, own, cumulative, _) in stats.stats.items():
        functions.append(
            {
                "file": filename,
                "line": line,
                "name": name,
                "calls": calls,
                "primitive_calls": primitive,
                "own_seconds": own,
                "cumulative_seconds": cumulative,
            }
        )

    cli_times = []
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory).resolve()
        left_path, right_path, answer = (
            folder / name for name in ("orig.txt", "edit.txt", "ans.txt")
        )
        left_path.write_text(original, encoding="utf-8")
        right_path.write_text(candidate, encoding="utf-8")
        for _ in range(3):
            start = time.perf_counter()
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(PROJECT / "main.py"),
                    str(left_path),
                    str(right_path),
                    str(answer),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            cli_times.append(time.perf_counter() - start)
            if result.returncode != 0 or answer.read_text().strip() != f"{expected:.2f}":
                raise RuntimeError(f"CLI benchmark failed: {result.stderr}")

    report = {
        "label": label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "seed": 3224004157,
        "original_characters": len(original),
        "candidate_characters": len(candidate),
        "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
        "score": expected,
        "repeats": repeats,
        "timing_seconds": timings,
        "median_seconds": statistics.median(timings),
        "tracemalloc_peak_bytes": peak,
        "cli_seconds": cli_times,
        "cli_median_seconds": statistics.median(cli_times),
        "functions": sorted(functions, key=lambda row: row["own_seconds"], reverse=True),
        "limitations": [
            "Synthetic data, not teacher fixtures or hidden tests.",
            "tracemalloc measures traced Python allocations, not whole-process RSS.",
            "cProfile overhead is excluded from timing; warmup and file I/O are separate.",
        ],
    }
    (output / f"{label}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    """Command-line entry for development measurements."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, choices=("baseline", "optimized"))
    parser.add_argument("--size", type=int, default=120000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, default=PROJECT / "reports" / "performance")
    arguments = parser.parse_args()
    if arguments.size < 20 or arguments.repeats < 1:
        parser.error("size must be at least 20 and repeats at least 1")
    report = run(arguments.label, arguments.output, arguments.size, arguments.repeats)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "label",
                    "score",
                    "median_seconds",
                    "tracemalloc_peak_bytes",
                    "cli_median_seconds",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
