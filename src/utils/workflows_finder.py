import os

class WorkflowsFinder:
    workflows_directory = "workflows"

    @classmethod
    def find(cls) -> list[str]:
        return [f"{cls.workflows_directory}/{f}" for f in os.listdir(cls.workflows_directory) if f.endswith(".json")]