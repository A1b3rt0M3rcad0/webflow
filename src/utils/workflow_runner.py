import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.core.entity.workflow import Workflow
from src.core.webflow import WebFlow
from src.core.workers.page_worker import PageWorker


def load_workflow_from_json(path: str | Path) -> Workflow:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Workflow não encontrado: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Workflow.model_validate(data)


def run_workflow_sync(workflow: Workflow) -> None:
    with sync_playwright() as playwright:
        webflow = WebFlow(playwright, PageWorker())
        webflow.run(workflow)


def run_workflow_from_file(path: str | Path) -> None:
    workflow = load_workflow_from_json(path)
    run_workflow_sync(workflow)
