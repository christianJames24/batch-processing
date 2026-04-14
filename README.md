# OpenAI Batch Example

Small Python example that submits a couple of requests through the OpenAI Batch API.

## What It Does

- Builds a tiny `.jsonl` batch input file
- Uploads it with `purpose="batch"`
- Creates a batch job for the `/v1/responses` endpoint
- Waits until the batch finishes and prints the results

## Requirements

- Python 3
- `openai`
- `python-dotenv`
- An `OPENAI_API_KEY` in `.env`

## Install

```powershell
py -3 -m pip install openai python-dotenv
```

## Run

Submit the batch and wait for completion:

```powershell
py -3 main.py
```

Check the status of an existing batch by ID:

```powershell
py -3 main.py --batch-id batch_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Watch an existing batch until it reaches a terminal status:

```powershell
py -3 main.py --batch-id batch_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --watch
```

Change polling frequency while waiting:

```powershell
py -3 main.py --batch-id batch_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --watch --poll-seconds 30
```

Run the same prompts synchronously so you can compare timings:

```powershell
py -3 sync_main.py
```

## Notes

- Batch jobs are asynchronous, so they are not the fastest way to get an immediate response.
- `main.py` now prints `Batch ID: ...` so you can re-attach to the same job later.
- This repo is just a minimal example, not a production workflow.
- The script writes `batch_input.jsonl` in the project folder before uploading it.

## Files

- [main.py](./main.py) - minimal batch submit and wait-for-results example
- [sync_main.py](./sync_main.py) - synchronous Responses API version for timing comparison
- [.env](./.env) - local environment variables

## OTHER SOURCES:
https://help.openai.com/en/articles/9197833-batch-api-faq
https://research-it.wharton.upenn.edu/programming/using-openai-batch-api/