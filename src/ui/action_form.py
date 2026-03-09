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
}


def build_action_params_form(parent, action_name: str, initial_params: dict | None) -> tuple[ttk.Frame, dict]:
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


def get_params_from_form(vars_dict: dict) -> dict | None:
    if not vars_dict:
        return None
    params = {}
    for key, (var, wtype) in vars_dict.items():
        val = var.get()
        if wtype == "entry_int":
            if str(val).strip():
                try:
                    params[key] = int(val)
                except ValueError:
                    params[key] = val
        elif wtype == "checkbox":
            params[key] = bool(val)
        elif wtype in ("entry", "combo"):
            s = str(val).strip()
            if s:
                params[key] = s
    return params if params else None
