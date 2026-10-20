import asyncio
import os
import sys
from pathlib import Path

from anthropic import AsyncAnthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import (
    CreateMessageResult,
    ErrorData,
    TextContent,
)


PROJECT_DIR = Path(__file__).resolve().parent
MODEL = "claude-sonnet-4-6"


async def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set ANTHROPIC_API_KEY before running this client.")

    async with AsyncAnthropic() as claude:

        async def handle_sampling(context, params):
            """Handle a sampling request received from our MCP server."""
            print("\n[CLIENT] Received a sampling request from the server.")

            # This learning example supports text-only sampling.
            if getattr(params, "tools", None):
                return ErrorData(
                    code=-32602,
                    message="This demo does not support sampling with tools.",
                )

            messages = []

            for message in params.messages:
                if not isinstance(message.content, TextContent):
                    return ErrorData(
                        code=-32602,
                        message="This demo supports text-only messages.",
                    )

                messages.append({
                    "role": message.role,
                    "content": message.content.text,
                })

            print("\nPrompt being sent to Claude:")
            for message in messages:
                print(message["content"])

            if params.system_prompt:
                print("\nSystem prompt:", params.system_prompt)

            approved = await asyncio.to_thread(
                input,
                "\nSend this request to Claude? [y/N]: ",
            )

            if approved.strip().lower() != "y":
                return ErrorData(
                    code=-32603,
                    message="User declined the sampling request.",
                )

            print("[CLIENT] Calling Claude...")

            response = await claude.messages.create(
                model=MODEL,
                max_tokens=min(params.max_tokens, 600),
                system=params.system_prompt or (
                    "Analyze the supplied reviews accurately and concisely."
                ),
                messages=messages,
            )

            text = "\n".join(
                block.text
                for block in response.content
                if block.type == "text"
            )

            if not text.strip():
                return ErrorData(
                    code=-32603,
                    message="Claude returned no text.",
                )

            print("\nClaude generated:")
            print(text)

            approved = await asyncio.to_thread(
                input,
                "\nReturn this response to the MCP server? [y/N]: ",
            )

            if approved.strip().lower() != "y":
                return ErrorData(
                    code=-32603,
                    message="User declined to share the response.",
                )

            print("[CLIENT] Returning the sampling response to the server.")

            return CreateMessageResult(
                role="assistant",
                model=response.model,
                content=TextContent(type="text", text=text),
                stop_reason=(
                    "maxTokens"
                    if response.stop_reason == "max_tokens"
                    else "endTurn"
                ),
            )

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(PROJECT_DIR / "server.py")],
            cwd=str(PROJECT_DIR),
            # The review tool doesn't need the park API token.
            # Don't pass the Anthropic key to the server.
            env={},
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(
                read,
                write,
                sampling_callback=handle_sampling,
            ) as session:
                await session.initialize()
                print("[CLIENT] Connected to the MCP server.")

                tools = await session.list_tools()
                print("Available tools:", [tool.name for tool in tools.tools])

                print("\n[CLIENT] Calling summarize_guest_reviews...")

                result = await session.call_tool(
                    "summarize_guest_reviews",
                    arguments={
                        "reviews": (
                            "The staff were friendly and check-in was easy.\n"
                            "Our site was clean, but Wi-Fi barely worked.\n"
                            "Great location, but bathrooms needed cleaning.\n"
                            "Helpful staff, but Wi-Fi kept disconnecting."
                        )
                    },
                )

                print("\n[CLIENT] Final tool result:")
                if result.is_error:
                    print("The tool reported an error.")

                for block in result.content:
                    if isinstance(block, TextContent):
                        print(block.text)


if __name__ == "__main__":
    asyncio.run(main())