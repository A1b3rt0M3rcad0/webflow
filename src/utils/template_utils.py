import re
from typing import Any

from src.core.entity.workflow import Workflow


TEMPLATE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


def extract_template_vars(workflow: Workflow) -> set[str]:  
    vars_found: set[str] = set()
    for browser in workflow.browsers:
        for page in browser.pages:
            for action in page.actions:
                if action.params:
                    _collect_vars(action.params, vars_found)
    return vars_found


def _collect_vars(obj: Any, out: set[str]) -> None:
    if isinstance(obj, str):
        for m in TEMPLATE_PATTERN.finditer(obj):
            out.add(m.group(1))
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_vars(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_vars(item, out)


def substitute_templates(workflow: Workflow, values: dict[str, str]) -> Workflow:
    data = workflow.model_dump(mode="json")

    def replace_in(obj: Any) -> Any:
        if isinstance(obj, str):
            for var, val in values.items():
                obj = obj.replace(f"{{{{{var}}}}}", val)
            return obj
        if isinstance(obj, dict):
            return {k: replace_in(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [replace_in(item) for item in obj]
        return obj

    data = replace_in(data)
    return Workflow.model_validate(data)
