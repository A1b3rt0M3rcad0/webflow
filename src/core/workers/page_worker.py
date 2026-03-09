from playwright.sync_api import Page
from ..entity.page_actions import (
    ElementDataType,
    Condition,
    EqualsCondition,
    NotEqualsCondition,
    ContainsCondition,
    NotContainsCondition,
    StartsWithCondition,
    EndsWithCondition,
    RegexMatchCondition,
    GreaterThanCondition,
    LessThanCondition,
    GreaterThanOrEqualCondition,
    LessThanOrEqualCondition,
    IsEmptyCondition,
    IsNotEmptyCondition,
    ExistsCondition,
    NotExistsCondition,
    IsVisibleCondition,
    IsHiddenCondition,
    IsEnabledCondition,
    IsDisabledCondition,
    HasClassCondition,
    NotHasClassCondition,
    HasAttributeCondition,
    NotHasAttributeCondition,
    AttributeEqualsCondition,
    AttributeNotEqualsCondition,
    AttributeContainsCondition,
    CountEqualsCondition,
    CountGreaterThanCondition,
    CountLessThanCondition,
    Action,
    ActionType,
)
from ..solvers.twocaptcha import TwoCaptchaSolver, RecaptchaSolver
import re

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

    @staticmethod
    def _extract_element_data(page: Page, selector: str, data_type: ElementDataType | str | None, attribute_name: str | None = None) -> str | None:
        """
        Extrai dados do elemento baseado no tipo especificado.
        
        Args:
            page: Página do Playwright
            selector: Seletor CSS do elemento
            data_type: Tipo de dado a extrair (text, html, value, attribute, id, class)
            attribute_name: Nome do atributo (quando data_type == "attribute")
        
        Returns:
            String com o valor extraído ou None
        """
        locator = page.locator(selector).first
        
        if data_type is None or isinstance(data_type, str):
            # Se for string, converter para enum
            if isinstance(data_type, str):
                try:
                    data_type = ElementDataType(data_type)
                except ValueError:
                    data_type = ElementDataType.TEXT  # Default
        
        if data_type == ElementDataType.TEXT or data_type is None:
            return locator.text_content() or ""
        elif data_type == ElementDataType.HTML:
            return locator.inner_html() or ""
        elif data_type == ElementDataType.VALUE:
            return locator.input_value() or ""
        elif data_type == ElementDataType.ATTRIBUTE:
            if not attribute_name:
                raise ValueError("attribute_name é obrigatório quando data_type é 'attribute'")
            return locator.get_attribute(attribute_name) or ""
        elif data_type == ElementDataType.ID:
            return locator.get_attribute("id") or ""
        elif data_type == ElementDataType.CLASS:
            return locator.get_attribute("class") or ""
        else:
            # Fallback para texto
            return locator.text_content() or ""

    @staticmethod
    def _evaluate_condition(page: Page, condition: Condition) -> bool:
        """Avalia uma condição e retorna True se for verdadeira, False caso contrário"""
        locator = page.locator(condition.selector)
        
        # Comparações de texto
        if isinstance(condition, EqualsCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return text.strip() == condition.value
        
        elif isinstance(condition, NotEqualsCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return text.strip() != condition.value
        
        elif isinstance(condition, ContainsCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return condition.value in text
        
        elif isinstance(condition, NotContainsCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return condition.value not in text
        
        elif isinstance(condition, StartsWithCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return text.strip().startswith(condition.value)
        
        elif isinstance(condition, EndsWithCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return text.strip().endswith(condition.value)
        
        elif isinstance(condition, RegexMatchCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            flags = 0
            if condition.flags:
                if "i" in condition.flags.lower():
                    flags |= re.IGNORECASE
            return bool(re.search(condition.pattern, text, flags))
        
        # Comparações numéricas
        elif isinstance(condition, GreaterThanCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            try:
                num = float(text.strip())
                return num > condition.value
            except ValueError:
                return False
        
        elif isinstance(condition, LessThanCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            try:
                num = float(text.strip())
                return num < condition.value
            except ValueError:
                return False
        
        elif isinstance(condition, GreaterThanOrEqualCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            try:
                num = float(text.strip())
                return num >= condition.value
            except ValueError:
                return False
        
        elif isinstance(condition, LessThanOrEqualCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            try:
                num = float(text.strip())
                return num <= condition.value
            except ValueError:
                return False
        
        # Verificações de estado
        elif isinstance(condition, IsEmptyCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return not text.strip()
        
        elif isinstance(condition, IsNotEmptyCondition):
            text = PageWorker._extract_element_data(
                page, condition.selector, condition.data_type, condition.attribute_name
            ) or ""
            return bool(text.strip())
        
        elif isinstance(condition, ExistsCondition):
            count = locator.count()
            return count > 0
        
        elif isinstance(condition, NotExistsCondition):
            count = locator.count()
            return count == 0
        
        elif isinstance(condition, IsVisibleCondition):
            try:
                return locator.first.is_visible()
            except Exception:
                return False
        
        elif isinstance(condition, IsHiddenCondition):
            try:
                return not locator.first.is_visible()
            except Exception:
                return True
        
        elif isinstance(condition, IsEnabledCondition):
            try:
                return locator.first.is_enabled()
            except Exception:
                return False
        
        elif isinstance(condition, IsDisabledCondition):
            try:
                return not locator.first.is_enabled()
            except Exception:
                return True
        
        # Verificações de atributos e classes
        elif isinstance(condition, HasClassCondition):
            try:
                classes = locator.first.get_attribute("class") or ""
                return condition.class_name in classes.split()
            except Exception:
                return False
        
        elif isinstance(condition, NotHasClassCondition):
            try:
                classes = locator.first.get_attribute("class") or ""
                return condition.class_name not in classes.split()
            except Exception:
                return True
        
        elif isinstance(condition, HasAttributeCondition):
            try:
                attr_value = locator.first.get_attribute(condition.attribute_name)
                if condition.attribute_value is None:
                    return attr_value is not None
                return attr_value == condition.attribute_value
            except Exception:
                return False
        
        elif isinstance(condition, NotHasAttributeCondition):
            try:
                attr_value = locator.first.get_attribute(condition.attribute_name)
                return attr_value is None
            except Exception:
                return True
        
        elif isinstance(condition, AttributeEqualsCondition):
            try:
                attr_value = locator.first.get_attribute(condition.attribute_name) or ""
                return attr_value == condition.value
            except Exception:
                return False
        
        elif isinstance(condition, AttributeNotEqualsCondition):
            try:
                attr_value = locator.first.get_attribute(condition.attribute_name) or ""
                return attr_value != condition.value
            except Exception:
                return True
        
        elif isinstance(condition, AttributeContainsCondition):
            try:
                attr_value = locator.first.get_attribute(condition.attribute_name) or ""
                return condition.value in attr_value
            except Exception:
                return False
        
        # Comparações de contagem
        elif isinstance(condition, CountEqualsCondition):
            count = locator.count()
            return count == condition.count
        
        elif isinstance(condition, CountGreaterThanCondition):
            count = locator.count()
            return count > condition.count
        
        elif isinstance(condition, CountLessThanCondition):
            count = locator.count()
            return count < condition.count
        
        else:
            print(f"[IF] Tipo de condição desconhecido: {type(condition)}")
            return False

    @staticmethod
    def _execute_actions(page: Page, actions: list[dict]):
        """Executa uma lista de ações"""
        # Importação local para evitar dependência circular
        from ..mappers import action_mapper
        
        for action_data in actions:
            action = Action(**action_data) if isinstance(action_data, dict) else action_data
            action_type = ActionType(action.name)
            fn = action_mapper(action_type)
            
            if action.params:
                # Converter dict para kwargs
                params = action.params if isinstance(action.params, dict) else {}
                fn(page, **params)
            else:
                fn(page)

    @staticmethod
    def _create_condition_from_dict(condition_data: dict) -> Condition:
        """Converte um dicionário em um objeto Condition"""
        # Se já for um objeto Condition, retornar diretamente
        if isinstance(condition_data, Condition):
            return condition_data
        
        # Mapear tipos de condição para classes
        condition_mapping = {
            "equals": EqualsCondition,
            "not_equals": NotEqualsCondition,
            "contains": ContainsCondition,
            "not_contains": NotContainsCondition,
            "starts_with": StartsWithCondition,
            "ends_with": EndsWithCondition,
            "regex_match": RegexMatchCondition,
            "greater_than": GreaterThanCondition,
            "less_than": LessThanCondition,
            "greater_than_or_equal": GreaterThanOrEqualCondition,
            "less_than_or_equal": LessThanOrEqualCondition,
            "is_empty": IsEmptyCondition,
            "is_not_empty": IsNotEmptyCondition,
            "exists": ExistsCondition,
            "not_exists": NotExistsCondition,
            "is_visible": IsVisibleCondition,
            "is_hidden": IsHiddenCondition,
            "is_enabled": IsEnabledCondition,
            "is_disabled": IsDisabledCondition,
            "has_class": HasClassCondition,
            "not_has_class": NotHasClassCondition,
            "has_attribute": HasAttributeCondition,
            "not_has_attribute": NotHasAttributeCondition,
            "attribute_equals": AttributeEqualsCondition,
            "attribute_not_equals": AttributeNotEqualsCondition,
            "attribute_contains": AttributeContainsCondition,
            "count_equals": CountEqualsCondition,
            "count_greater_than": CountGreaterThanCondition,
            "count_less_than": CountLessThanCondition,
        }
        
        # Tentar encontrar o tipo da condição
        condition_type = condition_data.get("type")
        if not condition_type:
            # Tentar inferir pelo formato: {"equals": {...}} ou diretamente {...}
            keys = list(condition_data.keys())
            if keys and keys[0] in condition_mapping:
                condition_type = keys[0]
                condition_data = condition_data[condition_type]
            else:
                # Fallback: assumir equals
                condition_type = "equals"
        
        condition_class = condition_mapping.get(condition_type)
        if not condition_class:
            raise ValueError(f"Tipo de condição desconhecido: {condition_type}")
        
        return condition_class(**condition_data)

    @staticmethod
    def if_action(
        page: Page,
        condition: dict,
        then: list[dict],
        else_: list[dict] | None = None,
    ):
        """
        Executa ações condicionalmente baseado em uma condição.
        
        Args:
            page: Página do Playwright
            condition: Dicionário com a condição a ser avaliada (ex: {"type": "equals", "selector": "...", "value": "..."})
            then: Lista de ações a executar se a condição for verdadeira
            else_: Lista de ações a executar se a condição for falsa (opcional)
        """
        print(f"[IF] Avaliando condição...")
        
        try:
            condition_obj = PageWorker._create_condition_from_dict(condition)
        except Exception as e:
            print(f"[IF] ✗ Erro ao criar condição: {e}")
            return
        
        # Avaliar condição
        result = PageWorker._evaluate_condition(page, condition_obj)
        
        print(f"[IF] Condição {'VERDADEIRA' if result else 'FALSA'}")
        
        # Executar ações apropriadas
        if result:
            if then:
                print(f"[IF] Executando {len(then)} ação(ões) do bloco THEN...")
                PageWorker._execute_actions(page, then)
                print(f"[IF] ✓ Bloco THEN executado")
        else:
            if else_:
                print(f"[IF] Executando {len(else_)} ação(ões) do bloco ELSE...")
                PageWorker._execute_actions(page, else_)
                print(f"[IF] ✓ Bloco ELSE executado")