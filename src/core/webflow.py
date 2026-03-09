from playwright.sync_api import Playwright
from .entity.workflow import Workflow
from .entity.page_actions import ActionType
from .workers.page_worker import PageWorker
from .mappers import browser_mapper, action_mapper

class WebFlow:

    def __init__(self, playwright: Playwright, page_worker: PageWorker):
        self.playwright = playwright
        self.page_worker = page_worker

    def run(self, workflow: Workflow):
        for browser in workflow.browsers:
            browser_instance = browser_mapper(self.playwright, browser.btype)()
            for page in browser.pages:
                page_instance = browser_instance.new_page()
                for action in page.actions:
                    fn = action_mapper(ActionType(action.name))
                    if action.params:
                        result = fn(page_instance, **action.params)
                    else:
                        result = fn(page_instance)
                    if result is not None:
                        print(result)
                page_instance.close()
            browser_instance.close()