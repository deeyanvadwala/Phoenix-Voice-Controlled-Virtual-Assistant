"""Start and stop the Phoenix microservices as separate processes."""
import subprocess
import sys
import time

import requests

from phoenix import config

SERVICES = ("tts", "llm", "web", "system", "gateway")


def start_services(env=None, startup_timeout=180):
    processes = {}
    for name in SERVICES:
        processes[name] = subprocess.Popen([sys.executable, "-m", f"phoenix.services.{name}_service"], env=env)
    try:
        _wait_until_healthy(processes, startup_timeout)
    except Exception:
        stop_services(processes)
        raise
    return processes


def _wait_until_healthy(processes, timeout):
    deadline = time.monotonic() + timeout
    pending = set(processes)
    while pending:
        for name in list(pending):
            if processes[name].poll() is not None:
                raise RuntimeError(f"{name} service exited with code {processes[name].returncode}")
            try:
                requests.get(config.service_url(name) + "/health", timeout=1).raise_for_status()
                pending.discard(name)
            except requests.RequestException:
                pass
        if pending and time.monotonic() > deadline:
            raise TimeoutError(f"services did not start in time: {', '.join(sorted(pending))}")
        if pending:
            time.sleep(0.5)


def stop_services(processes):
    for process in processes.values():
        if process.poll() is None:
            process.terminate()
    for process in processes.values():
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
