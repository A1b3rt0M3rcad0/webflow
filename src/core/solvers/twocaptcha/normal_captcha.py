from .solver import TwoCaptchaSolver
from typing import Dict, Any

class NormalCaptchaSolver:

    @staticmethod
    def solve(two_captcha_solver: TwoCaptchaSolver, file: str, **kwargs: Any) -> (Dict[str, str | Any] | None):
        solver = two_captcha_solver.create_solver()
        return solver.normal(file=file, **kwargs)