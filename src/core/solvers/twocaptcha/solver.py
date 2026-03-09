from twocaptcha import TwoCaptcha
import os

class TwoCaptchaSolver:

    @staticmethod
    def create_solver() -> TwoCaptcha:
        return TwoCaptcha(apiKey=os.getenv("2CAPTCHA_API_KEY"))