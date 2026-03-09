import os

class StepsFinder:
    steps_directory = "steps"

    @classmethod
    def find(cls) -> list[str]:
        files = [f for f in os.listdir(cls.steps_directory) if f.endswith(".json")]
        return sorted([f"{cls.steps_directory}/{f}" for f in files])