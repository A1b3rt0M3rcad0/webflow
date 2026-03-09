import queue
import sys
import threading
from io import StringIO
from typing import Callable

from playwright.sync_api import sync_playwright

from src.core.entity.workflow import Workflow
from src.core.webflow import WebFlow
from src.core.workers.page_worker import PageWorker


class StreamQueue:

    def __init__(self, log_queue: queue.Queue):
        self.log_queue = log_queue

    def write(self, text: str):
        if text:
            self.log_queue.put(text)

    def flush(self):
        pass


def run_workflow(workflow: Workflow, log_queue: queue.Queue, on_done: Callable[[bool, str | None], None]):
    def _run():
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stream = StreamQueue(log_queue)
        try:
            sys.stdout = stream
            sys.stderr = stream
            with sync_playwright() as playwright:
                webflow = WebFlow(playwright, PageWorker())
                webflow.run(workflow)
            if hasattr(on_done, "__call__"):
                on_done(True, None)
        except Exception as e:
            log_queue.put(f"\n[ERRO] {e}\n")
            if hasattr(on_done, "__call__"):
                on_done(False, str(e))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
