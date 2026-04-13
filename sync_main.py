import os
import time

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def elapsed_label(start_time):
    elapsed = time.time() - start_time
    return f"[{elapsed:.1f}s]"


def build_demo_prompts():
    return [
        "Reply in one short sentence: what is batch processing and what are the advantages and disadvantages of it (OPENAI)?",
        "Analysis on oshawott and piplup.",
    ]


def extract_text(response):
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    pieces = []
    for item in getattr(response, "output", []):
        for content in getattr(item, "content", []):
            text = getattr(content, "text", None)
            if text:
                pieces.append(text)

    return " ".join(pieces).strip() or "(no text found)"


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from your environment or .env file.")

    start_time = time.time()
    client = OpenAI()
    prompts = build_demo_prompts()

    print(f"{elapsed_label(start_time)} Starting synchronous requests...")

    for index, prompt in enumerate(prompts, start=1):
        request_start = time.time()
        response = client.responses.create(
            model="gpt-5.4-mini",
            input=prompt,
        )

        request_elapsed = time.time() - request_start
        print(f"{elapsed_label(start_time)} demo-{index} ({request_elapsed:.1f}s): {extract_text(response)}")

    print(f"{elapsed_label(start_time)} Finished all synchronous requests.")


if __name__ == "__main__":
    main()
