"""Compare response latency of the original single-process design with the microservices.

    python benchmark.py --runs 5 --mute

For every command it measures, on the same machine, model and prompt:
  * response latency: command received -> first audio starts playing
  * total time:       command received -> reply finished speaking

Runs alternate between the two architectures so load changes affect both equally.
Commands that open windows or change the volume are left out to avoid side effects.
Results are printed and saved to benchmark_results.json.
"""
import argparse
import json
import os
import statistics
import time

from phoenix import config

COMMANDS = [
    "how are you",
    "what time is it",
    "weather",
    "what is the capital of australia",
    "explain how a rainbow forms",
    "give me three tips for staying focused while studying",
    "what is the difference between a virus and a bacterium",
    "why do we have leap years",
]


def run_baseline(baseline, text):
    start = time.time()
    timing = baseline.handle(text)
    return timing["first_audio_at"] - start, timing["done_at"] - start


def run_services(gateway, tts, text):
    gateway.post("/reset", {"session_id": "benchmark"})  # same single-turn prompt as the baseline
    start = time.time()
    result = gateway.post("/command", {"text": text, "session_id": "benchmark"})
    if result.get("error"):
        raise RuntimeError(f"{text!r} failed: {result['error']}")
    status = tts.get(f"/wait/{result['request_id']}")
    return status["first_audio_at"] - start, status["done_at"] - start


def reduction(before, after):
    return 100 * (before - after) / before


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3, help="measured runs per command (after one warm-up)")
    parser.add_argument("--mute", action="store_true", help="speak at volume 0 (timing is unchanged)")
    args = parser.parse_args()

    if args.mute:
        os.environ["PHOENIX_TTS_VOLUME"] = "0"
        config.TTS_VOLUME = 0.0

    from phoenix.baseline import Baseline
    from phoenix.launcher import start_services, stop_services
    from phoenix.services.common import ServiceClient

    print("Starting services and warming up the model...")
    processes = start_services(env=os.environ.copy())
    try:
        baseline = Baseline()
        gateway = ServiceClient("gateway", timeout=300)
        tts = ServiceClient("tts", timeout=300)
        results = {text: {"baseline": [], "services": []} for text in COMMANDS}

        for run in range(args.runs + 1):
            label = "warm-up" if run == 0 else f"run {run}/{args.runs}"
            for text in COMMANDS:
                print(f"[{label}] {text}")
                measured = {"baseline": run_baseline(baseline, text), "services": run_services(gateway, tts, text)}
                if run:
                    for mode, value in measured.items():
                        results[text][mode].append(value)
    finally:
        stop_services(processes)

    report(results, args)


def report(results, args):
    def median(text, mode, index):
        return statistics.median(v[index] for v in results[text][mode])

    print(f"\nMedian of {args.runs} runs, model {config.LLM_MODEL}. Times in seconds.\n")
    header = f"{'command':<56} {'first audio: before -> after':>30} {'total: before -> after':>26}"
    print(header)
    print("-" * len(header))
    summary = {}
    for text in results:
        fb, fa = median(text, "baseline", 0), median(text, "services", 0)
        tb, ta = median(text, "baseline", 1), median(text, "services", 1)
        summary[text] = {"first_audio": [fb, fa], "total": [tb, ta]}
        print(
            f"{text:<56} {fb:>7.2f} -> {fa:>5.2f} ({reduction(fb, fa):>5.1f}%)"
            f" {tb:>7.2f} -> {ta:>5.2f} ({reduction(tb, ta):>5.1f}%)"
        )

    def overall(texts, key):
        before = statistics.mean(summary[t][key][0] for t in texts)
        after = statistics.mean(summary[t][key][1] for t in texts)
        return before, after, reduction(before, after)

    groups = {"all commands": list(results), "LLM questions": COMMANDS[3:], "built-in commands": COMMANDS[:3]}
    print()
    totals = {}
    for name, texts in groups.items():
        first, total = overall(texts, "first_audio"), overall(texts, "total")
        totals[name] = {"first_audio": first, "total": total}
        print(
            f"{name:<20} mean first audio {first[0]:.2f}s -> {first[1]:.2f}s ({first[2]:.1f}% lower), "
            f"mean total {total[0]:.2f}s -> {total[1]:.2f}s ({total[2]:.1f}% lower)"
        )

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump({"model": config.LLM_MODEL, "runs": args.runs, "raw": results, "medians": summary, "overall": totals}, f, indent=2)
    print("\nSaved benchmark_results.json")


if __name__ == "__main__":
    main()
