# dependencies = [
#   "httpx",
#   "websockets",
# ]
from __future__ import annotations

import asyncio
import sys

import httpx
import websockets


async def test_ping(base_url: str) -> bool:
    """Test the plain HTTP endpoint."""
    print("\n[HTTP /ping]")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{base_url}/ping")

    print("status:", response.status_code)
    print("body:", response.text)

    return response.is_success


async def test_sse(base_url: str) -> bool:
    """Test the SSE endpoint by reading a few streamed chunks."""
    print("\n[SSE /sse]")

    chunk_count = 0

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "GET",
            f"{base_url}/sse",
            headers={"Accept": "text/event-stream"},
        ) as response:
            print("status:", response.status_code)
            print("content-type:", response.headers.get("content-type"))

            if not response.is_success:
                print("SSE failed before stream started.")
                return False

            async for text_chunk in response.aiter_text():
                if not text_chunk.strip():
                    continue

                chunk_count += 1
                print(f"chunk {chunk_count}:")
                print(text_chunk.strip())

                if chunk_count >= 3:
                    break

    return chunk_count > 0


async def test_websocket(base_url: str) -> bool:
    """Test the WebSocket endpoint by sending and receiving one message."""
    print("\n[WebSocket /ws]")

    ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_url}/ws"

    try:
        async with websockets.connect(ws_url, open_timeout=10) as websocket:
            print("open: connected")

            first_message = await asyncio.wait_for(websocket.recv(), timeout=10)
            print("message:", first_message)

            await websocket.send("hello")

            second_message = await asyncio.wait_for(websocket.recv(), timeout=10)
            print("message:", second_message)

            return True

    except Exception as error:
        print("error:", str(error))
        return False


async def main() -> int:
    """Run all checks against the provided deployment URL."""
    if len(sys.argv) < 2:
        print("Usage: python verify.py https://your-deployment.vercel.app")
        return 1

    base_url = sys.argv[1].rstrip("/")

    try:
        http_ok = await test_ping(base_url)
    except Exception as error:
        print("[HTTP /ping] failed:", repr(error))
        http_ok = False

    try:
        sse_ok = await test_sse(base_url)
    except Exception as error:
        print("[SSE /sse] failed:", repr(error))
        sse_ok = False

    try:
        ws_ok = await test_websocket(base_url)
    except Exception as error:
        print("[WebSocket /ws] failed:", repr(error))
        ws_ok = False

    print("\n=== Summary ===")
    print("HTTP:", "OK" if http_ok else "FAIL")
    print("SSE :", "OK" if sse_ok else "FAIL")
    print("WS  :", "OK" if ws_ok else "FAIL")

    return 0 if ws_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))