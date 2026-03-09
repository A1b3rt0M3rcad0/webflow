import json
from pathlib import Path
from tkinter import ttk, messagebox, StringVar

from src.core.entity.workflow import Workflow
from src.core.entity.browser import Browser, BrowserType
from src.core.entity.page import Page
from src.core.entity.page_actions import Action
from src.ui.action_form import (
    ACTION_LABELS,
    build_action_params_form,
    get_params_from_form,
)


class ActionCard(ttk.Frame):

    def __init__(self, parent, action_data: dict, on_remove, on_change, **kwargs):
        super().__init__(parent, **kwargs)
        self.action_data = action_data
        self.on_remove = on_remove
        self.on_change = on_change
        self.vars_dict = {}
        self._build()

    def _build(self):
        row = ttk.Frame(self)
        row.pack(fill="x", pady=2)
        name = self.action_data.get("name", "goto")
        ttk.Label(row, text="Ação:").pack(side="left", padx=(0, 5))
        self.type_var = StringVar(value=name)
        types = list(ACTION_LABELS.keys())
        cb = ttk.Combobox(row, textvariable=self.type_var, values=types, width=30, state="readonly")
        cb.pack(side="left", padx=(0, 10))
        cb.bind("<<ComboboxSelected>>", self._on_type_change)
        ttk.Button(row, text="Remover", command=self.on_remove).pack(side="left", padx=2)
        ttk.Button(row, text="Subir", command=lambda: self.on_change("up")).pack(side="left", padx=2)
        ttk.Button(row, text="Descer", command=lambda: self.on_change("down")).pack(side="left", padx=2)

        self.params_frame = ttk.Frame(self)
        self.params_frame.pack(fill="x", padx=(20, 0), pady=5)
        self._rebuild_params()

    def _on_type_change(self, e=None):
        self.action_data["name"] = self.type_var.get()
        self.action_data["params"] = {}
        self._rebuild_params()
        self.on_change("type")

    def _rebuild_params(self):
        for w in self.params_frame.winfo_children():
            w.destroy()
        name = self.type_var.get()
        form_frame, self.vars_dict = build_action_params_form(
            self.params_frame, name, self.action_data.get("params")
        )
        form_frame.pack(fill="x")

    def get_data(self) -> dict:
        params = get_params_from_form(self.vars_dict)
        return {"name": self.type_var.get(), "params": params}


class StepEditor(ttk.Frame):
    def __init__(self, parent, steps_dir: str = "steps", on_save=None, on_test=None, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.steps_dir = Path(steps_dir)
        self.steps_dir.mkdir(parents=True, exist_ok=True)
        self.on_save = on_save
        self.on_test = on_test
        self.app = app
        self.current_path: str | None = None
        self.action_cards: list[ActionCard] = []
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=5, pady=5)

        row0 = ttk.Frame(top)
        row0.pack(fill="x", pady=(0, 6))
        ttk.Label(row0, text="Nome do step:").pack(side="left", padx=(0, 5))
        self.name_var = StringVar()
        ttk.Entry(row0, textvariable=self.name_var, width=30).pack(side="left", padx=(0, 10))

        row1 = ttk.Frame(top)
        row1.pack(fill="x")
        ttk.Button(row1, text="Novo", command=self._new).pack(side="left", padx=2)
        ttk.Button(row1, text="Salvar step", command=self._save).pack(side="left", padx=2)
        ttk.Button(row1, text="Testar", command=self._on_test).pack(side="left", padx=2)
        ttk.Button(row1, text="Carregar", command=self._load_selected).pack(side="left", padx=2)

        actions_frame = ttk.LabelFrame(self, text="Actions (clique em + para adicionar)")
        actions_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.cards_container = ttk.Frame(actions_frame)
        self.cards_container.pack(fill="both", expand=True, padx=5, pady=5)

        scroll_frame = ttk.Frame(actions_frame)
        scroll_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(scroll_frame, text="+ Adicionar action", command=self._add_action).pack(side="left", padx=2)
        self._new()

    def _add_action(self, action_data: dict | None = None):
        data = action_data or {"name": "goto", "params": {"url": "https://example.com"}}
        card = ActionCard(
            self.cards_container,
            data,
            on_remove=lambda: self._remove_card(card),
            on_change=lambda _: None,
        )
        card.pack(fill="x", pady=5)
        self.action_cards.append(card)
        self._update_card_order()

    def _remove_card(self, card: ActionCard):
        if card in self.action_cards:
            self.action_cards.remove(card)
            card.destroy()
            self._update_card_order()

    def _update_card_order(self):
        for i, card in enumerate(self.action_cards):
            card.on_change = lambda direction, c=card: self._move_card(c, direction)

    def _move_card(self, card: ActionCard, direction: str):
        idx = self.action_cards.index(card)
        if direction == "up" and idx > 0:
            self.action_cards[idx], self.action_cards[idx - 1] = self.action_cards[idx - 1], self.action_cards[idx]
        elif direction == "down" and idx < len(self.action_cards) - 1:
            self.action_cards[idx], self.action_cards[idx + 1] = self.action_cards[idx + 1], self.action_cards[idx]
        self._reorder_cards_ui()

    def _reorder_cards_ui(self):
        for card in self.action_cards:
            card.pack_forget()
        for card in self.action_cards:
            card.pack(fill="x", pady=5)

    def _on_test(self):
        if self.on_test:
            self.on_test()

    def _get_selected_step(self) -> str | None:
        if self.app and hasattr(self.app, "get_selected_step"):
            return self.app.get_selected_step()
        return None

    def _load_selected(self):
        path = self._get_selected_step()
        if path:
            self._load(path)
        else:
            messagebox.showinfo("Carregar", "Selecione um step na lista à esquerda.")

    def _new(self):
        self.current_path = None
        self.name_var.set("")
        for card in self.action_cards[:]:
            card.destroy()
        self.action_cards.clear()
        self._add_action({"name": "goto", "params": {"url": "https://example.com"}})

    def _load(self, path: str):
        p = Path(path)
        if not p.exists():
            messagebox.showerror("Erro", f"Arquivo não encontrado: {path}")
            return
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if "actions" not in data:
                raise ValueError("Step inválido: falta 'actions'")
            self.current_path = path
            self.name_var.set(p.stem)
            for card in self.action_cards[:]:
                card.destroy()
            self.action_cards.clear()
            for a in data["actions"]:
                self._add_action(a)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Salvar", "Informe o nome do step.")
            return
        data = self._to_dict()
        if not data["actions"]:
            messagebox.showerror("Erro", "Adicione pelo menos uma action.")
            return
        path = self.steps_dir / f"{name}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.current_path = str(path)
            messagebox.showinfo("Salvar", f"Step salvo em {path}")
            if self.on_save:
                self.on_save()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _to_dict(self) -> dict:
        return {"actions": [c.get_data() for c in self.action_cards]}

    def get_data(self) -> dict | None:
        return self._to_dict()

    def get_current_name(self) -> str | None:
        """Nome do step atual (arquivo ou campo Nome)."""
        if self.current_path:
            return Path(self.current_path).stem
        return self.name_var.get().strip() or None

    def get_workflow_for_test(self) -> Workflow | None:
        """Constrói um workflow temporário a partir do step para testar."""
        data = self._to_dict()
        if not data.get("actions"):
            return None
        actions = [Action(**a) for a in data["actions"]]
        page = Page(url="about:blank", actions=actions)
        browser = Browser(btype=BrowserType.CHROMIUM, pages=[page])
        return Workflow(browsers=[browser])
