import json
import os
import time
import argparse
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def elapsed_label(start_time):
    elapsed = time.time() - start_time
    return f"[{elapsed:.1f}s]"


def build_demo_requests():
    prompts = [
        "Reply in one short sentence: what is batch processing and what are the advantages and disadvantages of it (OPENAI)?",
        "Analysis on oshawott and piplup.",
    ]

    requests = []
    for index, prompt in enumerate(prompts, start=1):
        requests.append(
            {
                "custom_id": f"demo-{index}",
                "method": "POST",
                "url": "/v1/responses",
                "body": {
                    "model": "gpt-5.4-mini",
                    "input": prompt,
                },
            }
        )

    return requests


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row) + "\n")


def extract_text(result_line):
    response = result_line.get("response", {})
    body = response.get("body", {})

    output_text = body.get("output_text")
    if output_text:
        return output_text

    pieces = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                pieces.append(text)

    return " ".join(pieces).strip() or "(no text found)"


def print_results(client: OpenAI, batch, start_time):
    if not batch.output_file_id:
        print(f"{elapsed_label(start_time)} Batch completed but no output file was returned.")
        return

    output = client.files.content(batch.output_file_id)
    content = getattr(output, "text", None)
    if content is None:
        content = output.read().decode("utf-8")

    print(f"\n{elapsed_label(start_time)} Results:")
    for line in content.splitlines():
        result_line = json.loads(line)
        print(f"{elapsed_label(start_time)} {result_line['custom_id']}: {extract_text(result_line)}")


def watch_batch(client: OpenAI, batch, start_time, poll_seconds):
    terminal_statuses = {"completed", "failed", "expired", "cancelled"}

    while batch.status not in terminal_statuses:
        time.sleep(poll_seconds)
        batch = client.batches.retrieve(batch.id)
        print(f"{elapsed_label(start_time)} Current status: {batch.status}")

    return batch


def main():
    parser = argparse.ArgumentParser(description="Create or track an OpenAI batch job.")
    parser.add_argument("--batch-id", help="Track an existing batch by ID instead of creating a new one.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="When tracking by --batch-id, keep polling until the batch reaches a terminal status.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=5,
        help="Polling interval in seconds when waiting for batch status (default: 5).",
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from your environment or .env file.")

    if args.poll_seconds < 1:
        raise ValueError("--poll-seconds must be at least 1")

    start_time = time.time()
    client = OpenAI()

    if args.batch_id:
        batch = client.batches.retrieve(args.batch_id)
        print(f"Batch ID: {batch.id}")
        print(f"{elapsed_label(start_time)} Current status: {batch.status}")

        if not args.watch:
            print(f"{elapsed_label(start_time)} Re-run with --watch to keep polling this batch.")
            if batch.status == "completed":
                print_results(client, batch, start_time)
            return

        print(f"{elapsed_label(start_time)} Watching batch status...")
        batch = watch_batch(client, batch, start_time, args.poll_seconds)

        if batch.status != "completed":
            print(f"{elapsed_label(start_time)} Batch finished with status: {batch.status}")
            return

        print_results(client, batch, start_time)
        return

    input_path = Path("batch_input.jsonl")
    write_jsonl(input_path, build_demo_requests())

    with input_path.open("rb") as file_handle:
        uploaded_file = client.files.create(file=file_handle, purpose="batch")

    batch = client.batches.create(
        input_file_id=uploaded_file.id,
        endpoint="/v1/responses",
        completion_window="24h",
    )

    print(f"Batch ID: {batch.id}")
    print(f"{elapsed_label(start_time)} Created batch: {batch.id}")
    print(f"{elapsed_label(start_time)} Initial status: {batch.status}")
    print(f"{elapsed_label(start_time)} Waiting for the batch to finish...")

    batch = watch_batch(client, batch, start_time, args.poll_seconds)

    if batch.status != "completed":
        print(f"{elapsed_label(start_time)} Batch finished with status: {batch.status}")
        return

    print_results(client, batch, start_time)


if __name__ == "__main__":
    main()
