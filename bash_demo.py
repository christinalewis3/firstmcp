import os
import subprocess
from pathlib import Path

from anthropic import Anthropic


PROJECT_DIR = Path(__file__).resolve().parent
MODEL = "claude-sonnet-4-6"

# Only these exact commands can run in this learning demo.
ALLOWED_COMMANDS = {
    "pwd",
    "ls *.py",
    "wc -l *.py",
}


def execute_bash(tool_input: dict) -> tuple[str, bool]:
    """Return command output and whether the tool encountered an error."""

    if tool_input.get("restart"):
        return "This demo uses a fresh shell for each command.", False

    command = tool_input.get("command")

    if command not in ALLOWED_COMMANDS:
        return (
            "Command rejected. Use exactly one of: "
            + ", ".join(sorted(ALLOWED_COMMANDS)),
            True,
        )

    print(f"\n[PYTHON] Claude requested: {command}")

    try:
        result = subprocess.run(
            ["/bin/bash", "--noprofile", "--norc", "-c", command],
            cwd=PROJECT_DIR,
            # Don't pass API credentials into the shell.
            env={"PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = (
            f"Exit code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(output)
        return output[:12000], result.returncode != 0

    except subprocess.TimeoutExpired:
        return "Command timed out after 10 seconds.", True


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set ANTHROPIC_API_KEY before running this demo.")

    messages = [
        {
            "role": "user",
            "content": (
                "Inspect my Python project using the bash tool. "
                "First list its Python filenames, then count their lines. "
                "Explain what you observed. "
                "You may use only these exact commands: "
                "'pwd', 'ls *.py', and 'wc -l *.py'. "
                "Each command runs in a fresh shell in the project folder."
            ),
        }
    ]

    with Anthropic() as client:
        for turn in range(5):
            print(f"\n[PYTHON] Sending request {turn + 1} to Claude...")

            response = client.messages.create(
                model=MODEL,
                max_tokens=1200,
                tools=[
                    {
                        "type": "bash_20250124",
                        "name": "bash",
                    }
                ],
                messages=messages,
            )

            # Preserve Claude's complete response, including tool-use IDs.
            messages.append({
                "role": "assistant",
                "content": [
                    block.model_dump(mode="json")
                    for block in response.content
                ],
            })

            tool_results = []

            for block in response.content:
                if block.type == "text":
                    print(f"\n[CLAUDE] {block.text}")

                elif block.type == "tool_use":
                    if block.name == "bash":
                        output, is_error = execute_bash(block.input)
                    else:
                        output, is_error = "Unknown tool.", True

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                        "is_error": is_error,
                    })

            if not tool_results:
                print(f"\n[PYTHON] Finished: {response.stop_reason}")
                return

            # Send the shell output back so Claude can continue.
            messages.append({
                "role": "user",
                "content": tool_results,
            })

        print("\n[PYTHON] Stopped after the five-request limit.")


if __name__ == "__main__":
    main()