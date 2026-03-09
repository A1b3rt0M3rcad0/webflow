from playwright.sync_api import Playwright, Browser, Page
from .entity.browser import BrowserType
from .entity.page_actions import ActionType
from .workers.page_worker import PageWorker
from typing import Callable, Dict, Any

def browser_mapper(playwright: Playwright, browser_type: BrowserType) -> Callable[[], Browser]:
    browsers = {
        BrowserType.CHROMIUM: playwright.chromium.launch,
        BrowserType.FIREFOX: playwright.firefox.launch,
        BrowserType.WEBKIT: playwright.webkit.launch,
    }
    return browsers[browser_type]

def action_mapper(action_name: ActionType) -> Callable:
    actions = {
        ActionType.GOTO: PageWorker.goto,
        ActionType.SCREENSHOT: PageWorker.screenshot,
        ActionType.TITLE: PageWorker.title,
        ActionType.CLICK: PageWorker.click,
        ActionType.FILL: PageWorker.fill,
        ActionType.WAIT_FOR_SELECTOR: PageWorker.wait_for_selector,
        ActionType.GET_ELEMENT_DATA: PageWorker.get_element_data,
        ActionType.SOLVE_RECAPTCHA_V2_AND_INJECT: PageWorker.solve_recaptcha_v2_and_inject,
        ActionType.IF: PageWorker.if_action,
    }
    return actions[action_name]