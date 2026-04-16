import argparse
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def format_timestamp(timestamp):
    if not timestamp:
        return "n/a"

    return datetime.fromtimestamp(timestamp).isoformat()


def extract_text(response):
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    pieces = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "message":
            continue

        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                pieces.append(text)

    return " ".join(pieces).strip()


def extract_function_calls(response):
    calls = []
    tool_like_item_types = {
        "function_call",
        "custom_tool_call",
        "file_search_call",
        "web_search_call",
        "computer_call",
        "code_interpreter_call",
        "local_shell_call",
        "function_shell_call",
        "apply_patch_call",
        "mcp_call",
        "mcp_approval_request",
        "mcp_list_tools",
    }

    for item in getattr(response, "output", []) or []:
        item_type = getattr(item, "type", None)
        if item_type not in tool_like_item_types:
            continue

        calls.append(
            {
                "type": item_type,
                "name": getattr(item, "name", None),
                "call_id": getattr(item, "call_id", None),
                "arguments": getattr(item, "arguments", None),
                "status": getattr(item, "status", None),
                "output": getattr(item, "output", None),
                "error": getattr(item, "error", None),
            }
        )

    return calls


def main():
    parser = argparse.ArgumentParser(description="Retrieve the status of an OpenAI response by ID.")
    parser.add_argument("response_id", help="The response ID to look up, for example resp_123...")
    parser.add_argument(
        "--show-text",
        action="store_true",
        help="Print any text returned with the response when available.",
    )
    parser.add_argument(
        "--show-tool-calls",
        action="store_true",
        help="Print function/tool call outputs when the response completed without assistant text.",
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from your environment or .env file.")

    client = OpenAI()
    response = client.responses.retrieve(args.response_id)

    print(f"Response ID: {response.id}")
    print(f"Status: {getattr(response, 'status', 'unknown')}")
    print(f"Model: {getattr(response, 'model', 'unknown')}")
    print(f"Created At: {format_timestamp(getattr(response, 'created_at', None))}")
    print(f"Completed At: {format_timestamp(getattr(response, 'completed_at', None))}")

    error = getattr(response, "error", None)
    if error:
        print(f"Error: {error}")

    if args.show_text:
        text = extract_text(response)
        print(f"Output Text: {text or '(no text found)'}")

    if args.show_tool_calls:
        calls = extract_function_calls(response)
        if not calls:
            print("Tool Calls: (none found)")
        else:
            print("Tool Calls:")
            for index, call in enumerate(calls, start=1):
                print(f"  {index}. Type: {call['type'] or 'unknown'}")
                print(f"     Name: {call['name'] or 'n/a'}")
                print(f"     Call ID: {call['call_id'] or 'n/a'}")
                print(f"     Status: {call['status'] or 'unknown'}")
                arguments = call["arguments"]
                if arguments:
                    try:
                        parsed = json.loads(arguments)
                        formatted = json.dumps(parsed, indent=2, ensure_ascii=True)
                    except json.JSONDecodeError:
                        formatted = arguments

                    print("     Arguments:")
                    for line in formatted.splitlines():
                        print(f"       {line}")

                output = call["output"]
                if output:
                    print("     Output:")
                    for line in str(output).splitlines():
                        print(f"       {line}")

                error_text = call["error"]
                if error_text:
                    print(f"     Error: {error_text}")

    if args.show_text and not args.show_tool_calls and not extract_text(response):
        calls = extract_function_calls(response)
        if calls:
            print("Note: This response contains function/tool call output rather than assistant text.")
            print("Re-run with --show-tool-calls to inspect it.")


if __name__ == "__main__":
    main()
