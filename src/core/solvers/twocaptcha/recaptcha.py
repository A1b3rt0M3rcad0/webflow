from .solver import TwoCaptchaSolver
from typing import Dict, Any

class RecaptchaSolver:

    @staticmethod
    def solve_v3(two_captcha_solver: TwoCaptchaSolver, sitekey: str, url: str, **kwargs: Any) -> (Dict[str, str | Any] | None):
        solver = two_captcha_solver.create_solver()
        return solver.recaptcha(sitekey=sitekey, url=url, version="v3", **kwargs)
    
    @staticmethod
    def solve_v2(two_captcha_solver: TwoCaptchaSolver, sitekey: str, url: str, **kwargs: Any) -> (Dict[str, str | Any] | None):
        solver = two_captcha_solver.create_solver()
        return solver.recaptcha(sitekey=sitekey, url=url, version="v2", **kwargs)