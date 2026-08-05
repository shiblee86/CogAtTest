"""Minimal synchronous Chrome DevTools Protocol client.

The app under test is a vanilla-JS single page app with no build step and no
Node toolchain in this repo, so instead of a JS test runner (Jest/Vitest) the
suite drives the *real* app in a real headless browser and asserts on the
live JS state / DOM. This module is the thin CDP transport that makes that
possible from plain pytest.

A background thread owns the asyncio event loop + websocket connection so
the rest of the suite can call plain synchronous methods.
"""
import asyncio
import base64
import json
import threading

import websockets


class JSError(RuntimeError):
    """Raised when a Runtime.evaluate call throws inside the page."""


class CDPSession:
    def __init__(self, ws_url):
        self._id = 0
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        fut = asyncio.run_coroutine_threadsafe(self._connect(ws_url), self._loop)
        fut.result(15)

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _connect(self, ws_url):
        self.ws = await websockets.connect(ws_url, max_size=None)

    def _next_id(self):
        self._id += 1
        return self._id

    async def _send_async(self, method, params):
        mid = self._next_id()
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == mid:
                return msg

    def send(self, method, params=None, timeout=20):
        fut = asyncio.run_coroutine_threadsafe(self._send_async(method, params), self._loop)
        return fut.result(timeout)

    def evaluate(self, expression, timeout=20):
        """Evaluate a JS expression in the page and return its JSON-serializable value.

        Raises JSError if the expression throws.
        """
        resp = self.send(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            timeout=timeout,
        )
        result = resp.get("result", {})
        inner = result.get("result", {})
        if "exceptionDetails" in result or inner.get("subtype") == "error":
            desc = inner.get("description") or json.dumps(result.get("exceptionDetails"))
            raise JSError(f"{expression!r} raised: {desc}")
        return inner.get("value")

    def navigate(self, url, ready_expr="document.querySelectorAll('.subtest-card').length > 0", timeout=15):
        # Top-level `const`/`function` declarations in app.js (e.g. FIGURE_TYPES)
        # become available as soon as the script parses -- but renderHome()
        # itself only runs inside a DOMContentLoaded listener. Waiting on
        # rendered cards (not just "the script loaded") avoids a race where a
        # test starts before the home screen has actually been built.
        import time

        self.send("Runtime.enable")
        self.send("Page.navigate", {"url": url})
        deadline = time.time() + timeout
        last_err = None
        while time.time() < deadline:
            try:
                if self.evaluate(ready_expr):
                    return
            except JSError as e:
                last_err = e
            time.sleep(0.1)
        raise TimeoutError(f"navigate() ready condition never became true: {ready_expr}; last error: {last_err}")

    def click(self, selector):
        self.evaluate(f"document.querySelector({json.dumps(selector)}).click()")

    def screenshot(self, path):
        resp = self.send("Page.captureScreenshot", {"format": "png"})
        data = base64.b64decode(resp["result"]["data"])
        with open(path, "wb") as f:
            f.write(data)

    def close(self):
        async def _close():
            try:
                await self.ws.close()
            except Exception:
                pass

        fut = asyncio.run_coroutine_threadsafe(_close(), self._loop)
        try:
            fut.result(5)
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
