from pydantic import BaseModel, Field
from typing import Dict, Any, Union, List, Optional
from enum import Enum

class ActionType(Enum):
    GOTO = "goto"
    SCREENSHOT = "screenshot"
    TITLE = "title"
    CLICK = "click"
    FILL = "fill"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    GET_ELEMENT_DATA = "get_element_data"
    SOLVE_RECAPTCHA_V2_AND_INJECT = "solve_recaptcha_v2_and_inject"
    IF = "if"

class ElementDataType(Enum):
    TEXT = "text"
    HTML = "html"
    ATTRIBUTE = "attribute"
    VALUE = "value"
    ID = "id"
    CLASS = "class"

class RecaptchaVersion(Enum):
    V3 = "v3"
    V2 = "v2"

class Action(BaseModel):
    name: str
    params: Union[Dict[str, Any], None]

class GoToActionParams(BaseModel):
    url: str

class ScreenShotActionParams(BaseModel):
    path: str

class SolveNormalCaptchaActionParams(BaseModel):
    file: str

class SolveRecaptchaActionParams(BaseModel):
    version: RecaptchaVersion
    sitekey: str
    url: str

class ClickActionParams(BaseModel):
    selector: str
    force: bool = False

class FillActionParams(BaseModel):
    selector: str
    text: str
    delay: int | None = None

class WaitForSelectorActionParams(BaseModel):
    selector: str
    timeout: int | None = None

class GetElementDataActionParams(BaseModel):
    selector: str
    data_type: ElementDataType
    attribute_name: str | None = None


class SolveRecaptchaV2AndInjectParams(BaseModel):
    sitekey: str | None = None
    sitekey_selector: str | None = None  # ex: "[data-sitekey]" - obtém da página
    url: str | None = None  # se None, usa page.url
    max_retries: int = 3  # tentativas até conseguir resolver

# ============================================================================
# CONDIÇÕES DE COMPARAÇÃO DE TEXTO
# ============================================================================

class EqualsCondition(BaseModel):
    """Verifica se o valor do elemento é igual ao valor especificado"""
    selector: str
    value: str
    data_type: ElementDataType | None = None  # Tipo de dado a extrair (text, html, value, attribute, id, class)
    attribute_name: str | None = None  # Nome do atributo (quando data_type == "attribute")

class NotEqualsCondition(BaseModel):
    """Verifica se o valor do elemento é diferente do valor especificado"""
    selector: str
    value: str
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class ContainsCondition(BaseModel):
    """Verifica se o valor do elemento contém o valor especificado"""
    selector: str
    value: str
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class NotContainsCondition(BaseModel):
    """Verifica se o valor do elemento não contém o valor especificado"""
    selector: str
    value: str
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class StartsWithCondition(BaseModel):
    """Verifica se o valor do elemento começa com o valor especificado"""
    selector: str
    value: str
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class EndsWithCondition(BaseModel):
    """Verifica se o valor do elemento termina com o valor especificado"""
    selector: str
    value: str
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class RegexMatchCondition(BaseModel):
    """Verifica se o valor do elemento corresponde à expressão regular especificada"""
    selector: str
    pattern: str  # Expressão regular
    flags: str | None = None  # Flags opcionais (ex: "i" para case-insensitive)
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

# ============================================================================
# CONDIÇÕES DE COMPARAÇÃO NUMÉRICA
# ============================================================================

class GreaterThanCondition(BaseModel):
    """Verifica se o valor numérico do elemento é maior que o valor especificado"""
    selector: str
    value: float
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class LessThanCondition(BaseModel):
    """Verifica se o valor numérico do elemento é menor que o valor especificado"""
    selector: str
    value: float
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class GreaterThanOrEqualCondition(BaseModel):
    """Verifica se o valor numérico do elemento é maior ou igual ao valor especificado"""
    selector: str
    value: float
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class LessThanOrEqualCondition(BaseModel):
    """Verifica se o valor numérico do elemento é menor ou igual ao valor especificado"""
    selector: str
    value: float
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

# ============================================================================
# CONDIÇÕES DE VERIFICAÇÃO DE ESTADO DO ELEMENTO
# ============================================================================

class IsEmptyCondition(BaseModel):
    """Verifica se o elemento está vazio (sem texto ou valor)"""
    selector: str
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class IsNotEmptyCondition(BaseModel):
    """Verifica se o elemento não está vazio (tem texto ou valor)"""
    selector: str
    data_type: ElementDataType | None = None
    attribute_name: str | None = None

class ExistsCondition(BaseModel):
    """Verifica se o elemento existe no DOM"""
    selector: str

class NotExistsCondition(BaseModel):
    """Verifica se o elemento não existe no DOM"""
    selector: str

class IsVisibleCondition(BaseModel):
    """Verifica se o elemento está visível na página"""
    selector: str

class IsHiddenCondition(BaseModel):
    """Verifica se o elemento está oculto na página"""
    selector: str

class IsEnabledCondition(BaseModel):
    """Verifica se o elemento está habilitado (não desabilitado)"""
    selector: str

class IsDisabledCondition(BaseModel):
    """Verifica se o elemento está desabilitado"""
    selector: str

# ============================================================================
# CONDIÇÕES DE VERIFICAÇÃO DE ATRIBUTOS E CLASSES CSS
# ============================================================================

class HasClassCondition(BaseModel):
    """Verifica se o elemento possui a classe CSS especificada"""
    selector: str
    class_name: str

class NotHasClassCondition(BaseModel):
    """Verifica se o elemento não possui a classe CSS especificada"""
    selector: str
    class_name: str

class HasAttributeCondition(BaseModel):
    """Verifica se o elemento possui o atributo especificado"""
    selector: str
    attribute_name: str
    attribute_value: str | None = None  # Se especificado, verifica também o valor

class NotHasAttributeCondition(BaseModel):
    """Verifica se o elemento não possui o atributo especificado"""
    selector: str
    attribute_name: str

class AttributeEqualsCondition(BaseModel):
    """Verifica se o valor do atributo do elemento é igual ao valor especificado"""
    selector: str
    attribute_name: str
    value: str

class AttributeNotEqualsCondition(BaseModel):
    """Verifica se o valor do atributo do elemento é diferente do valor especificado"""
    selector: str
    attribute_name: str
    value: str

class AttributeContainsCondition(BaseModel):
    """Verifica se o valor do atributo do elemento contém o valor especificado"""
    selector: str
    attribute_name: str
    value: str

# ============================================================================
# CONDIÇÕES DE COMPARAÇÃO DE CONTAGEM DE ELEMENTOS
# ============================================================================

class CountEqualsCondition(BaseModel):
    """Verifica se a quantidade de elementos correspondentes ao seletor é igual ao valor especificado"""
    selector: str
    count: int

class CountGreaterThanCondition(BaseModel):
    """Verifica se a quantidade de elementos correspondentes ao seletor é maior que o valor especificado"""
    selector: str
    count: int

class CountLessThanCondition(BaseModel):
    """Verifica se a quantidade de elementos correspondentes ao seletor é menor que o valor especificado"""
    selector: str
    count: int

# ============================================================================
# UNION DE TODAS AS CONDIÇÕES
# ============================================================================

Condition = Union[
    # Comparações de texto
    EqualsCondition,
    NotEqualsCondition,
    ContainsCondition,
    NotContainsCondition,
    StartsWithCondition,
    EndsWithCondition,
    RegexMatchCondition,
    # Comparações numéricas
    GreaterThanCondition,
    LessThanCondition,
    GreaterThanOrEqualCondition,
    LessThanOrEqualCondition,
    # Verificações de estado
    IsEmptyCondition,
    IsNotEmptyCondition,
    ExistsCondition,
    NotExistsCondition,
    IsVisibleCondition,
    IsHiddenCondition,
    IsEnabledCondition,
    IsDisabledCondition,
    # Verificações de atributos e classes
    HasClassCondition,
    NotHasClassCondition,
    HasAttributeCondition,
    NotHasAttributeCondition,
    AttributeEqualsCondition,
    AttributeNotEqualsCondition,
    AttributeContainsCondition,
    # Comparações de contagem
    CountEqualsCondition,
    CountGreaterThanCondition,
    CountLessThanCondition,
]

class IfActionParams(BaseModel):
    condition: Condition
    then: List[Action]
    else_: List[Action] = Field(default_factory=list)