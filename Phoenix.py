"""Start Phoenix: launches the microservices, then the voice client.

    python Phoenix.py                  # services + voice assistant
    python Phoenix.py --services-only  # just the services (e.g. to call the gateway over HTTP)
    python Phoenix.py --text           # type commands instead of speaking them
"""
import argparse
import sys

from phoenix.client import VoiceClient
from phoenix.launcher import start_services, stop_services


def main():
    parser = argparse.ArgumentParser(description="Phoenix voice assistant")
    parser.add_argument("--services-only", action="store_true", help="run the services without the voice client")
    parser.add_argument("--text", action="store_true", help="read commands from the keyboard instead of the microphone")
    args = parser.parse_args()

    print("Starting Phoenix services...")
    processes = start_services()
    try:
        if args.services_only:
            print("Services running. Press Ctrl+C to stop.")
            for process in processes.values():
                process.wait()
        elif args.text:
            print("Type a command and press Enter (Ctrl+C to quit).")
            VoiceClient().run_text(sys.stdin)
        else:
            VoiceClient().run()
    except KeyboardInterrupt:
        pass
    finally:
        stop_services(processes)


if __name__ == "__main__":
    main()
