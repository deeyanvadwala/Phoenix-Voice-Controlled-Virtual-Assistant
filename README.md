# Phoenix – Voice-Controlled Virtual Assistant

Phoenix is a Python voice assistant that runs system and web automation tasks from spoken
commands and answers open-ended questions with LLaMA 3 (through LangChain and Ollama). It
remembers earlier turns of the conversation. The backend is split into Flask microservices,
so speech output, LLM generation and actions run in parallel instead of one after another.

## Architecture

```
 microphone ──► Voice client ──HTTP──► Gateway :5000 ──► LLM service :5001     (LangChain + LLaMA 3, chat memory)
 (wake word,                              │        ├──► Web service :5002     (sites, search, weather + cache)
  speech-to-text)                         │        └──► System service :5003  (apps, volume, time)
                                          └─────────────► TTS service :5004    (one long-lived speech engine)
```

| Service | File | Responsibility |
|---|---|---|
| Gateway | `phoenix/services/gateway_service.py` | Parses the command into an intent, calls the service that owns it, sends the reply to TTS |
| LLM | `phoenix/services/llm_service.py` | Multi-turn conversation with `RunnableWithMessageHistory`, separate history for each session (trimmed to the last 20 messages), token streaming |
| Web | `phoenix/services/web_service.py` | Opens websites, Google/YouTube search, weather from wttr.in with a 10-minute cache |
| System | `phoenix/services/system_service.py` | Launches Calculator, Notepad, CMD and Explorer; volume control; current time |
| TTS | `phoenix/services/tts_service.py` | Queues speech and plays it in order on a single engine, and records when audio starts |
| Voice client | `phoenix/client.py` | Wake word, Google speech recognition, conversation loop |

### Where the parallelism comes from

- **LLM answers are spoken while they are still being generated.** The gateway streams tokens
  from the LLM service, splits them into sentences (`SentenceChunker`) and sends each sentence to
  the TTS service right away. The TTS service plays sentence 1 while the model writes sentence 2.
  In the original design, nothing was spoken until the whole answer had been generated.
- **Speech never blocks actions.** TTS runs in its own process, so "Opening Calculator" plays
  while the system service launches the app.
- **No repeated start-up costs.** The TTS engine is created once rather than on every reply. HTTP
  connections between services are reused. The model is loaded into memory when the LLM service
  starts, and Ollama keeps it loaded. Weather results are cached.

## Benchmark

`benchmark.py` compares the microservices with `phoenix/baseline.py`, a single-process copy of
the original design. The copy runs everything sequentially, creates the speech engine on every
reply, generates the whole LLM answer before speaking, and fetches the weather every time. Both
sides use the same model, prompt, sampling settings (temperature 0, fixed seed) and commands.
They take turns command by command, so any change in machine load affects both equally.

```bash
python benchmark.py --runs 3 --mute   # --mute plays audio at volume 0; timing is unchanged
```

It reports **response latency** (from receiving the command to the first audio playing) and
**total time** (until the reply has finished playing). Results are saved to
`benchmark_results.json`.

Results on a Windows 11 laptop with `llama3` running locally (median of 3 runs per command):

| | Before (single process) | After (microservices) | Change |
|---|---|---|---|
| Response latency, mean over 8 commands | 1.59 s | 0.58 s | **64% lower** |
| Response latency, LLM questions | 2.45 s | 0.91 s | 63% lower |
| Weather (cache hit) | 0.41 s | 0.03 s | 92% lower |
| Time to finish speaking, LLM questions | 34.1 s | 35.8 s | about the same (5% slower) |

The improvement is in how soon Phoenix starts answering. The total time to speak a long answer
does not improve. Each sentence is currently played with its own TTS call, and that per-call
overhead cancels out the time saved by generating and speaking in parallel.

## Setup

Requirements: Python 3.10+, Windows (the app launcher and SAPI5 voices are Windows-specific), a
microphone, and [Ollama](https://ollama.com) with the model pulled:

```bash
ollama pull llama3
pip install -r requirements.txt
```

## Running

```bash
python Phoenix.py                  # starts all services, then the voice assistant
python Phoenix.py --services-only  # only the services, for use over HTTP
python Phoenix.py --text           # type commands instead of speaking (no microphone needed)
```

Say **"Phoenix"** to wake it, then for example:

| Say | Result |
|---|---|
| "open calculator" / "open notepad" / "open command prompt" | Launches the app |
| "open youtube" / "open google" / "open my mail" | Opens the site |
| "search google for flask tutorials", "play lofi music on youtube" | Runs a search |
| "what time is it", "weather", "weather in Boston" | Speaks the answer |
| "volume up" / "volume down" | Changes the system volume |
| anything else | Answered by LLaMA 3, with memory of earlier turns |
| "go to sleep" / "terminate" | Waits for the wake word again / exits |

You can also send commands to the gateway directly, without speaking:

```bash
curl -X POST http://127.0.0.1:5000/command -H "Content-Type: application/json" \
     -d "{\"text\": \"what is the capital of australia\", \"session_id\": \"demo\"}"
```

Settings such as ports, model, voice, wake word and weather city are set with `PHOENIX_*`
environment variables (see `phoenix/config.py`).

## Tests

```bash
python -m unittest discover -s tests -t .
```

The tests use fake versions of the model, the speech engine and the downstream services, so they
need no microphone, speakers or Ollama.
