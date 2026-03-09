import json
from pathlib import Path

from src.core.entity.workflow import Workflow
from src.core.entity.browser import Browser, BrowserType
from src.core.entity.page import Page
from src.core.entity.page_actions import Action


class MakeWorkflowByStep:

    default_url = "about:blank"
    default_browser = BrowserType.CHROMIUM
    workflows_directory = "workflows"

    @classmethod
    def make(
        cls,
        steps_paths: list[str],
        url: str | None = None,
        browser_type: BrowserType | str = None,
        output_name: str | None = None,
        save: bool = True,
    ) -> Workflow:

        all_actions: list[Action] = []
        page_url = url or cls.default_url

        for step_path in steps_paths:
            path = Path(step_path)
            if not path.exists():
                raise FileNotFoundError(f"Step não encontrado: {step_path}")

            with open(path, encoding="utf-8") as f:
                step = json.load(f)

            if "actions" not in step:
                raise ValueError(f"Step inválido (falta 'actions'): {step_path}")

            for action_data in step["actions"]:
                all_actions.append(
                    Action(
                        name=action_data["name"],
                        params=action_data.get("params"),
                    )
                )

            if "url" in step and not url:
                page_url = step["url"]

        btype = browser_type or cls.default_browser
        if isinstance(btype, str):
            btype = BrowserType(btype)

        page = Page(url=page_url, actions=all_actions)
        browser = Browser(btype=btype, pages=[page])
        workflow = Workflow(browsers=[browser])
        if save:
            cls._save(workflow, steps_paths, output_name)
        return workflow

    @classmethod
    def _save(cls, workflow: Workflow, steps_paths: list[str], output_name: str | None) -> None:
        Path(cls.workflows_directory).mkdir(parents=True, exist_ok=True)
        if output_name is None:
            names = [Path(p).stem for p in steps_paths]
            output_name = "_".join(names)
        output_path = Path(cls.workflows_directory) / f"{output_name}.json"
        data = workflow.model_dump(mode="json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
