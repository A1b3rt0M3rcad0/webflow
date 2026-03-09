from playwright.sync_api import Page
from ..entity.page_actions import ElementDataType
from ..solvers.twocaptcha import TwoCaptchaSolver, RecaptchaSolver

try:
    from twocaptcha.exceptions.api import ApiException as TwoCaptchaApiException
except ImportError:
    TwoCaptchaApiException = Exception  # fallback se pacote mudar

class PageWorker:

    @staticmethod
    def goto(page: Page, url: str):
        print(f"[GOTO] Navegando para: {url}")
        page.goto(url)
        print(f"[GOTO] ✓ Página carregada")
    
    @staticmethod
    def screenshot(page: Page, path: str):
        print(f"[SCREENSHOT] Salvando em: {path}")
        page.screenshot(path=path)
        print(f"[SCREENSHOT] ✓ Captura salva")
    
    @staticmethod
    def title(page: Page) -> str:
        print(f"[TITLE] Obtendo título da página...")
        result = page.title()
        print(f"[TITLE] ✓ Título: {result!r}")
        return result
    
    @staticmethod
    def click(page: Page, selector: str, force: bool = False):
        extra = " (force=True)" if force else ""
        print(f"[CLICK] Clicando em: {selector!r}{extra}")
        page.locator(selector).click(force=force)
        print(f"[CLICK] ✓ Clique executado")
    
    @staticmethod
    def fill(page: Page, selector: str, text: str, delay: int | None = None, force: bool = False):
        opts = []
        if delay is not None:
            opts.append(f"delay={delay}ms")
        if force:
            opts.append("force=True")
        extra = f" ({', '.join(opts)})" if opts else ""
        print(f"[FILL] Preenchendo {selector!r} com {text!r}{extra}")
        locator = page.locator(selector)
        fill_opts = {"force": force} if force else {}
        if delay is not None:
            locator.fill("", **fill_opts)
            locator.press_sequentially(text, delay=delay)
        else:
            locator.fill(text, **fill_opts)
        print(f"[FILL] ✓ Campo preenchido")
    
    @staticmethod
    def wait_for_selector(page: Page, selector: str, timeout: int | None = None):
        timeout_str = f"{timeout}ms" if timeout else "default"
        print(f"[WAIT_FOR_SELECTOR] Aguardando {selector!r} (timeout: {timeout_str})")
        locator = page.locator(selector)
        if timeout is not None:
            locator.wait_for(state="visible", timeout=timeout)
        else:
            locator.wait_for(state="visible")
        print(f"[WAIT_FOR_SELECTOR] ✓ Elemento visível")
    
    @staticmethod
    def get_element_data(
        page: Page,
        selector: str,
        data_type: str,
        attribute_name: str | None = None,
    ) -> str | None:
        extra = f", attribute_name={attribute_name!r}" if attribute_name else ""
        print(f"[GET_ELEMENT_DATA] selector={selector!r}, data_type={data_type!r}{extra}")
        locator = page.locator(selector).first
        dt = ElementDataType(data_type) if isinstance(data_type, str) else data_type
        
        if dt == ElementDataType.TEXT:
            result = locator.text_content()
        elif dt == ElementDataType.HTML:
            result = locator.inner_html()
        elif dt == ElementDataType.VALUE:
            result = locator.input_value()
        elif dt == ElementDataType.ATTRIBUTE:
            if not attribute_name:
                raise ValueError("attribute_name é obrigatório quando data_type é 'attribute'")
            result = locator.get_attribute(attribute_name)
        else:
            result = None
        preview = (result[:80] + "…") if result and len(result) > 80 else result
        print(f"[GET_ELEMENT_DATA] ✓ Obtido: {preview!r}")
        return result

    @staticmethod
    def solve_recaptcha_v2_and_inject(
        page: Page,
        sitekey: str | None = None,
        sitekey_selector: str | None = None,
        url: str | None = None,
        max_retries: int = 3,
    ):
        print(f"[SOLVE_RECAPTCHA_V2] sitekey={sitekey!r}, sitekey_selector={sitekey_selector!r}, url={url!r}, max_retries={max_retries}")
        if not sitekey and not sitekey_selector:
            raise ValueError("sitekey ou sitekey_selector é obrigatório")
        if sitekey_selector:
            sitekey = page.locator(sitekey_selector).first.get_attribute("data-sitekey")
            if not sitekey:
                raise ValueError(f"sitekey não encontrado no seletor {sitekey_selector}")
            print(f"[SOLVE_RECAPTCHA_V2] Sitekey obtido da página: {sitekey!r}")
        page_url = url or page.url
        solver = TwoCaptchaSolver()
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[SOLVE_RECAPTCHA_V2] Tentativa {attempt}/{max_retries} - Enviando para 2Captcha (30-90s)...")
                result = RecaptchaSolver.solve_v2(solver, sitekey=sitekey, url=page_url)
                if not result or "code" not in result:
                    raise RuntimeError("Falha ao resolver reCAPTCHA")
                break
            except TwoCaptchaApiException as e:
                last_error = e
                err_msg = str(e)
                print(f"[SOLVE_RECAPTCHA_V2] ✗ Tentativa {attempt} falhou: {err_msg}")
                if attempt < max_retries:
                    print(f"[SOLVE_RECAPTCHA_V2] Retentando em 2s...")
                    page.wait_for_timeout(2000)
                else:
                    raise RuntimeError(f"reCAPTCHA não resolvido após {max_retries} tentativas. Último erro: {err_msg}") from e
        token = result["code"]
        print(f"[SOLVE_RECAPTCHA_V2] ✓ Token recebido ({len(token)} chars), injetando na página...")
        page.evaluate(
            """
            (token) => {
                const textarea = document.getElementById("g-recaptcha-response")
                    || document.querySelector("[name=g-recaptcha-response]");
                if (textarea) {
                    textarea.value = token;
                    textarea.innerHTML = token;
                }
                const callback = window.___grecaptcha_cfg?.clients?.[0]?.o?.o?.callback;
                if (typeof callback === "function") callback(token);
                else if (typeof callback === "string" && window[callback]) window[callback](token);
            }
            """,
            token,
        )
        print(f"[SOLVE_RECAPTCHA_V2] ✓ Token injetado com sucesso")