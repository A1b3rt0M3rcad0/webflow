from tkinter import ttk, StringVar, BooleanVar, IntVar

ACTION_FIELDS = {
    "goto": [
        ("URL ({{var}} = template)", "url", "entry", "https://example.com", None),
    ],
    "screenshot": [
        ("Caminho do arquivo", "path", "entry", "screenshot.png", None),
    ],
    "title": [],
    "click": [
        ("Seletor (ex: button#submit)", "selector", "entry", "", None),
        ("Forçar clique (ignorar disabled)", "force", "checkbox", False, None),
    ],
    "fill": [
        ("Seletor", "selector", "entry", "input[name='email']", None),
        ("Texto ({{var}} = template)", "text", "entry", "", None),
        ("Delay entre teclas (ms, 0=instantâneo)", "delay", "entry_int", "", None),
        ("Forçar (inputs disabled)", "force", "checkbox", False, None),
    ],
    "wait_for_selector": [
        ("Seletor", "selector", "entry", "div[class='content']", None),
        ("Timeout (ms)", "timeout", "entry_int", "10000", None),
    ],
    "get_element_data": [
        ("Seletor", "selector", "entry", "div[class='result']", None),
        ("Tipo de dado", "data_type", "combo", "text", ["text", "html", "attribute", "value"]),
        ("Nome do atributo (se data_type=attribute)", "attribute_name", "entry", "", None),
    ],
    "solve_recaptcha_v2_and_inject": [
        ("Sitekey", "sitekey", "entry", "", None),
        ("Seletor sitekey", "sitekey_selector", "entry", "[data-sitekey]", None),
        ("Tentativas", "max_retries", "entry_int", "5", None),
    ],
}

ACTION_LABELS = {
    "goto": "Ir para URL",
    "screenshot": "Capturar tela",
    "title": "Obter título",
    "click": "Clicar",
    "fill": "Preencher campo",
    "wait_for_selector": "Aguardar elemento",
    "get_element_data": "Obter dado do elemento",
    "solve_recaptcha_v2_and_inject": "Resolver reCAPTCHA v2",
    "if": "Se (condição)",
}

# Tipos de condições disponíveis
CONDITION_TYPES = [
    ("equals", "Igual a"),
    ("not_equals", "Diferente de"),
    ("contains", "Contém"),
    ("not_contains", "Não contém"),
    ("starts_with", "Começa com"),
    ("ends_with", "Termina com"),
    ("regex_match", "Regex (corresponde)"),
    ("greater_than", "Maior que (número)"),
    ("less_than", "Menor que (número)"),
    ("greater_than_or_equal", "Maior ou igual (número)"),
    ("less_than_or_equal", "Menor ou igual (número)"),
    ("is_empty", "Está vazio"),
    ("is_not_empty", "Não está vazio"),
    ("exists", "Existe no DOM"),
    ("not_exists", "Não existe no DOM"),
    ("is_visible", "Está visível"),
    ("is_hidden", "Está oculto"),
    ("is_enabled", "Está habilitado"),
    ("is_disabled", "Está desabilitado"),
    ("has_class", "Tem classe CSS"),
    ("not_has_class", "Não tem classe CSS"),
    ("has_attribute", "Tem atributo"),
    ("not_has_attribute", "Não tem atributo"),
    ("attribute_equals", "Atributo igual a"),
    ("attribute_not_equals", "Atributo diferente de"),
    ("attribute_contains", "Atributo contém"),
    ("count_equals", "Quantidade igual a"),
    ("count_greater_than", "Quantidade maior que"),
    ("count_less_than", "Quantidade menor que"),
]


def build_action_params_form(parent, action_name: str, initial_params: dict | None) -> tuple[ttk.Frame, dict]:
    # Ação IF tem UI especial
    if action_name == "if":
        return build_if_action_form(parent, initial_params)
    
    fields = ACTION_FIELDS.get(action_name, [])
    frame = ttk.Frame(parent)
    vars_dict = {}

    for i, (label, key, wtype, default, extra) in enumerate(fields):
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label + ":", width=35, anchor="w").pack(side="left", padx=(0, 5))

        val = (initial_params or {}).get(key, default)
        if wtype == "entry":
            v = StringVar(value=str(val) if val is not None else "")
            ttk.Entry(row, textvariable=v, width=40).pack(side="left", fill="x", expand=True)
            vars_dict[key] = (v, "entry")
        elif wtype == "entry_int":
            v = StringVar(value=str(val) if val not in (None, "") else "")
            ttk.Entry(row, textvariable=v, width=15).pack(side="left")
            vars_dict[key] = (v, "entry_int")
        elif wtype == "checkbox":
            v = BooleanVar(value=bool(val))
            ttk.Checkbutton(row, variable=v).pack(side="left")
            vars_dict[key] = (v, "checkbox")
        elif wtype == "combo":
            v = StringVar(value=str(val) if val else (extra[0] if extra else ""))
            ttk.Combobox(row, textvariable=v, values=extra or [], width=20).pack(side="left")
            vars_dict[key] = (v, "combo")

    return frame, vars_dict


def build_if_action_form(parent, initial_params: dict | None) -> tuple[ttk.Frame, dict]:
    """Constrói formulário especial para ação IF"""
    frame = ttk.Frame(parent)
    vars_dict = {}
    
    # Buscar o IfActionCard através da referência armazenada no params_frame
    def find_if_action_card():
        """Busca o card (IfActionCard ou ActionCard com métodos IF) através da referência armazenada"""
        # Primeiro verificar o próprio parent (params_frame)
        print(f"[DEBUG find_if_action_card] Verificando parent: {parent}")
        print(f"[DEBUG find_if_action_card] Tipo do parent: {type(parent).__name__}")
        print(f"[DEBUG find_if_action_card] Tem _if_action_card_ref: {hasattr(parent, '_if_action_card_ref')}")
        if hasattr(parent, '_if_action_card_ref'):
            ref = parent._if_action_card_ref
            print(f"[DEBUG] Encontrado _if_action_card_ref em parent: {parent}, referência: {ref}")
            # Verificar se o card tem o método necessário (_edit_then abre o editor completo)
            if ref and hasattr(ref, '_edit_then'):
                print(f"[DEBUG] Card encontrado tem método _edit_then")
                return ref
            else:
                print(f"[DEBUG] Card encontrado mas sem método _edit_then, tentando adicionar...")
                # Tentar adicionar método se não existir
                if ref and not hasattr(ref, '_edit_then'):
                    if hasattr(ref, '_create_edit_then_method'):
                        ref._edit_then = ref._create_edit_then_method()
                        print(f"[DEBUG] Método _edit_then adicionado dinamicamente")
                return ref
        
        # Se não encontrou, procurar na hierarquia acima
        current = parent
        for i in range(10):
            if hasattr(current, 'master') and current.master:
                current = current.master
                print(f"[DEBUG find_if_action_card] Verificando nível {i+1}: {current}, tipo: {type(current).__name__}")
                if hasattr(current, '_if_action_card_ref'):
                    ref = current._if_action_card_ref
                    print(f"[DEBUG] Encontrado _if_action_card_ref em: {current}, referência: {ref}")
                    # Verificar se o card tem o método necessário
                    if ref and hasattr(ref, '_edit_then'):
                        return ref
            else:
                break
        print(f"[DEBUG] Não encontrou _if_action_card_ref na hierarquia")
        return None
    
    params = initial_params or {}
    condition = params.get("condition", {})
    condition_type = condition.get("type") or "equals"
    
    # Tipo de condição
    row = ttk.Frame(frame)
    row.pack(fill="x", pady=5)
    ttk.Label(row, text="Tipo de condição:", width=20, anchor="w").pack(side="left", padx=(0, 5))
    condition_type_var = StringVar(value=condition_type)
    condition_types_values = [ct[0] for ct in CONDITION_TYPES]
    condition_types_labels = {ct[0]: ct[1] for ct in CONDITION_TYPES}
    cb = ttk.Combobox(row, textvariable=condition_type_var, values=condition_types_values, width=30, state="readonly")
    cb.pack(side="left")
    vars_dict["condition_type"] = (condition_type_var, "combo")
    
    # Seletor (sempre necessário)
    row = ttk.Frame(frame)
    row.pack(fill="x", pady=2)
    ttk.Label(row, text="Seletor:", width=20, anchor="w").pack(side="left", padx=(0, 5))
    selector_var = StringVar(value=condition.get("selector", ""))
    ttk.Entry(row, textvariable=selector_var, width=40).pack(side="left", fill="x", expand=True)
    vars_dict["selector"] = (selector_var, "entry")
    
    # Tipo de dado a extrair
    row = ttk.Frame(frame)
    row.pack(fill="x", pady=2)
    ttk.Label(row, text="Tipo de dado:", width=20, anchor="w").pack(side="left", padx=(0, 5))
    data_type_var = StringVar(value=condition.get("data_type", "text"))
    data_type_options = ["text", "html", "value", "attribute", "id", "class"]
    cb_data_type = ttk.Combobox(row, textvariable=data_type_var, values=data_type_options, width=20, state="readonly")
    cb_data_type.pack(side="left")
    vars_dict["data_type"] = (data_type_var, "combo")
    
    # Nome do atributo (quando data_type == "attribute")
    attr_name_row = ttk.Frame(frame)
    attr_name_row.pack(fill="x", pady=2)
    ttk.Label(attr_name_row, text="Nome do atributo:", width=20, anchor="w").pack(side="left", padx=(0, 5))
    attr_name_var = StringVar(value=condition.get("attribute_name", ""))
    attr_name_entry = ttk.Entry(attr_name_row, textvariable=attr_name_var, width=40)
    attr_name_entry.pack(side="left", fill="x", expand=True)
    vars_dict["attribute_name"] = (attr_name_var, "entry")
    
    def update_attr_name_visibility(*args):
        """Mostra/esconde campo de nome do atributo baseado no data_type"""
        if data_type_var.get() == "attribute":
            attr_name_row.pack(fill="x", pady=2, before=condition_fields_frame)
        else:
            attr_name_row.pack_forget()
    
    data_type_var.trace("w", update_attr_name_visibility)
    update_attr_name_visibility()  # Chamar inicialmente
    
    # Campos condicionais baseados no tipo
    condition_fields_frame = ttk.Frame(frame)
    condition_fields_frame.pack(fill="x", pady=5)
    
    def update_condition_fields(*args):
        """Atualiza campos baseado no tipo de condição selecionado"""
        for w in condition_fields_frame.winfo_children():
            w.destroy()
        
        ct = condition_type_var.get()
        new_row = ttk.Frame(condition_fields_frame)
        new_row.pack(fill="x", pady=2)
        
        # Campos específicos por tipo
        if ct in ["equals", "not_equals", "contains", "not_contains", "starts_with", "ends_with", "attribute_equals", "attribute_not_equals", "attribute_contains"]:
            ttk.Label(new_row, text="Valor:", width=20, anchor="w").pack(side="left", padx=(0, 5))
            value_var = StringVar(value=condition.get("value", ""))
            ttk.Entry(new_row, textvariable=value_var, width=40).pack(side="left", fill="x", expand=True)
            vars_dict["value"] = (value_var, "entry")
        elif ct == "regex_match":
            ttk.Label(new_row, text="Padrão (regex):", width=20, anchor="w").pack(side="left", padx=(0, 5))
            pattern_var = StringVar(value=condition.get("pattern", ""))
            ttk.Entry(new_row, textvariable=pattern_var, width=40).pack(side="left", fill="x", expand=True)
            vars_dict["pattern"] = (pattern_var, "entry")
            row2 = ttk.Frame(condition_fields_frame)
            row2.pack(fill="x", pady=2)
            ttk.Label(row2, text="Flags (ex: i=case-insensitive):", width=20, anchor="w").pack(side="left", padx=(0, 5))
            flags_var = StringVar(value=condition.get("flags", ""))
            ttk.Entry(row2, textvariable=flags_var, width=20).pack(side="left")
            vars_dict["flags"] = (flags_var, "entry")
        elif ct in ["greater_than", "less_than", "greater_than_or_equal", "less_than_or_equal"]:
            ttk.Label(new_row, text="Valor numérico:", width=20, anchor="w").pack(side="left", padx=(0, 5))
            value_var = StringVar(value=str(condition.get("value", "")))
            ttk.Entry(new_row, textvariable=value_var, width=20).pack(side="left")
            vars_dict["value"] = (value_var, "entry_float")
        elif ct in ["has_class", "not_has_class"]:
            ttk.Label(new_row, text="Nome da classe:", width=20, anchor="w").pack(side="left", padx=(0, 5))
            class_var = StringVar(value=condition.get("class_name", ""))
            ttk.Entry(new_row, textvariable=class_var, width=40).pack(side="left", fill="x", expand=True)
            vars_dict["class_name"] = (class_var, "entry")
        elif ct in ["has_attribute", "not_has_attribute", "attribute_equals", "attribute_not_equals", "attribute_contains"]:
            ttk.Label(new_row, text="Nome do atributo:", width=20, anchor="w").pack(side="left", padx=(0, 5))
            attr_var = StringVar(value=condition.get("attribute_name", ""))
            ttk.Entry(new_row, textvariable=attr_var, width=40).pack(side="left", fill="x", expand=True)
            vars_dict["attribute_name"] = (attr_var, "entry")
            if ct == "has_attribute":
                row2 = ttk.Frame(condition_fields_frame)
                row2.pack(fill="x", pady=2)
                ttk.Label(row2, text="Valor do atributo (opcional):", width=20, anchor="w").pack(side="left", padx=(0, 5))
                attr_value_var = StringVar(value=condition.get("attribute_value", ""))
                ttk.Entry(row2, textvariable=attr_value_var, width=40).pack(side="left", fill="x", expand=True)
                vars_dict["attribute_value"] = (attr_value_var, "entry")
        elif ct in ["count_equals", "count_greater_than", "count_less_than"]:
            ttk.Label(new_row, text="Quantidade:", width=20, anchor="w").pack(side="left", padx=(0, 5))
            count_var = StringVar(value=str(condition.get("count", "")))
            ttk.Entry(new_row, textvariable=count_var, width=20).pack(side="left")
            vars_dict["count"] = (count_var, "entry_int")
    
    condition_type_var.trace("w", update_condition_fields)
    update_condition_fields()  # Chamar inicialmente
    
    # Botão único para editar ações THEN/ELSE
    btn_frame = ttk.LabelFrame(frame, text="Ações THEN e ELSE")
    btn_frame.pack(fill="x", padx=5, pady=10)
    
    params = initial_params or {}
    then_count = len(params.get("then", []))
    else_count = len(params.get("else_", []))
    total_count = then_count + else_count
    
    btn_inner = ttk.Frame(btn_frame)
    btn_inner.pack(fill="x", padx=5, pady=5)
    
    # Handler único que abre o editor completo com abas THEN/ELSE
    def on_edit_actions_click():
        print(f"[DEBUG] Botão Editar Actions CLICADO!")
        card = find_if_action_card()
        print(f"[DEBUG] Card encontrado: {card}")
        if card:
            # Usar _edit_then que abre o editor completo (que tem abas THEN/ELSE)
            if hasattr(card, '_edit_then'):
                print(f"[DEBUG] Chamando _edit_then do card para abrir editor completo: {card}")
                try:
                    card._edit_then()
                except Exception as e:
                    print(f"[DEBUG] ERRO ao chamar _edit_then: {e}")
                    import traceback
                    traceback.print_exc()
            elif hasattr(card, '_edit_actions'):
                # Se tiver método específico _edit_actions, usar ele
                print(f"[DEBUG] Chamando _edit_actions do card: {card}")
                try:
                    card._edit_actions()
                except Exception as e:
                    print(f"[DEBUG] ERRO ao chamar _edit_actions: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[DEBUG] ERRO: Card não tem métodos _edit_then ou _edit_actions")
        else:
            print(f"[DEBUG] ERRO: Card não encontrado")
    
    edit_btn = ttk.Button(btn_inner, text=f"✏️ Editar Actions ({total_count} ação(ões) total)", 
                         command=on_edit_actions_click)
    edit_btn.pack(fill="x", padx=5, pady=2)
    print(f"[DEBUG] Botão Editar Actions criado: {edit_btn}")
    
    # Armazenar referência para atualizar texto depois
    vars_dict["_edit_actions_button"] = (edit_btn, "button")
    print(f"[DEBUG] Botão armazenado no vars_dict. Chaves: {list(vars_dict.keys())}")
    
    return frame, vars_dict


def get_params_from_form(vars_dict: dict, action_name: str = None) -> dict | None:
    if not vars_dict:
        return None
    
    # Ação IF tem tratamento especial
    if action_name == "if":
        return get_if_params_from_form(vars_dict)
    
    params = {}
    for key, (var, wtype) in vars_dict.items():
        val = var.get()
        if wtype == "entry_int":
            if str(val).strip():
                try:
                    params[key] = int(val)
                except ValueError:
                    params[key] = val
        elif wtype == "entry_float":
            if str(val).strip():
                try:
                    params[key] = float(val)
                except ValueError:
                    params[key] = val
        elif wtype == "checkbox":
            params[key] = bool(val)
        elif wtype in ("entry", "combo"):
            s = str(val).strip()
            if s:
                params[key] = s
    return params if params else None


def get_if_params_from_form(vars_dict: dict) -> dict | None:
    """Extrai parâmetros do formulário IF"""
    condition_type = vars_dict.get("condition_type", (None, None))[0]
    if not condition_type:
        return None
    
    condition_type_val = condition_type.get()
    
    # Construir objeto de condição
    condition = {"type": condition_type_val}
    
    # Adicionar campos comuns
    if "selector" in vars_dict:
        selector_val = vars_dict["selector"][0].get().strip()
        if selector_val:
            condition["selector"] = selector_val
    
    # Adicionar data_type
    if "data_type" in vars_dict:
        data_type_val = vars_dict["data_type"][0].get().strip()
        if data_type_val:
            condition["data_type"] = data_type_val
    
    # Adicionar attribute_name (quando data_type == "attribute" ou tipos específicos)
    if "attribute_name" in vars_dict:
        attr_name_val = vars_dict["attribute_name"][0].get().strip()
        if attr_name_val:
            condition["attribute_name"] = attr_name_val
    
    # Adicionar campos específicos do tipo
    if condition_type_val in ["equals", "not_equals", "contains", "not_contains", "starts_with", "ends_with", "attribute_equals", "attribute_not_equals", "attribute_contains"]:
        if "value" in vars_dict:
            value_val = vars_dict["value"][0].get().strip()
            if value_val:
                condition["value"] = value_val
    elif condition_type_val == "regex_match":
        if "pattern" in vars_dict:
            pattern_val = vars_dict["pattern"][0].get().strip()
            if pattern_val:
                condition["pattern"] = pattern_val
        if "flags" in vars_dict:
            flags_val = vars_dict["flags"][0].get().strip()
            if flags_val:
                condition["flags"] = flags_val
    elif condition_type_val in ["greater_than", "less_than", "greater_than_or_equal", "less_than_or_equal"]:
        if "value" in vars_dict:
            value_val = vars_dict["value"][0].get().strip()
            if value_val:
                try:
                    condition["value"] = float(value_val)
                except ValueError:
                    condition["value"] = value_val
    elif condition_type_val in ["has_class", "not_has_class"]:
        if "class_name" in vars_dict:
            class_val = vars_dict["class_name"][0].get().strip()
            if class_val:
                condition["class_name"] = class_val
    elif condition_type_val in ["has_attribute", "not_has_attribute", "attribute_equals", "attribute_not_equals", "attribute_contains"]:
        if "attribute_name" in vars_dict:
            attr_val = vars_dict["attribute_name"][0].get().strip()
            if attr_val:
                condition["attribute_name"] = attr_val
        if condition_type_val == "has_attribute" and "attribute_value" in vars_dict:
            attr_value_val = vars_dict["attribute_value"][0].get().strip()
            if attr_value_val:
                condition["attribute_value"] = attr_value_val
        elif condition_type_val in ["attribute_equals", "attribute_not_equals", "attribute_contains"]:
            if "value" in vars_dict:
                value_val = vars_dict["value"][0].get().strip()
                if value_val:
                    condition["value"] = value_val
    elif condition_type_val in ["count_equals", "count_greater_than", "count_less_than"]:
        if "count" in vars_dict:
            count_val = vars_dict["count"][0].get().strip()
            if count_val:
                try:
                    condition["count"] = int(count_val)
                except ValueError:
                    condition["count"] = count_val
    
    # THEN e ELSE serão preenchidos pelo editor de ações
    return {
        "condition": condition,
        "then": [],  # Será preenchido pelo editor
        "else_": [],  # Será preenchido pelo editor
    }
