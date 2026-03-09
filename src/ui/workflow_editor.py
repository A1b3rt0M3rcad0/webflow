"""
Editor de workflows - arraste steps ou adicione actions.
JSON fica por baixo dos panos.
"""
import json
from pathlib import Path
from tkinter import ttk, messagebox, Toplevel, StringVar

from src.core.entity.workflow import Workflow
from src.core.entity.browser import Browser, BrowserType
from src.core.entity.page import Page
from src.core.entity.page_actions import Action
from src.utils.make_workflows_by_step import MakeWorkflowByStep
from src.ui.action_form import build_action_params_form, get_params_from_form, ACTION_LABELS


class WorkflowActionCard(ttk.Frame):
    """Card de action no workflow (modo manual)."""

    def __init__(self, parent, action_data: dict, on_remove, on_move, **kwargs):
        super().__init__(parent, **kwargs)
        self.action_data = action_data
        self.on_remove = on_remove
        self.on_move = on_move
        self.vars_dict = {}
        self._build()

    def _build(self):
        row = ttk.Frame(self)
        row.pack(fill="x", pady=2)
        name = self.action_data.get("name", "goto")
        self.type_var = StringVar(value=name)
        types = list(ACTION_LABELS.keys())
        cb = ttk.Combobox(row, textvariable=self.type_var, values=types, width=28, state="readonly")
        cb.pack(side="left", padx=(0, 5))
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_type_change())
        ttk.Button(row, text="X", width=3, command=self.on_remove).pack(side="left", padx=2)
        ttk.Button(row, text="▲", width=3, command=lambda: self.on_move("up")).pack(side="left", padx=2)
        ttk.Button(row, text="▼", width=3, command=lambda: self.on_move("down")).pack(side="left", padx=2)

        self.params_frame = ttk.Frame(self)
        self.params_frame.pack(fill="x", padx=(20, 0), pady=3)
        self._rebuild_params()

    def _on_type_change(self):
        self.action_data["name"] = self.type_var.get()
        self.action_data["params"] = {}
        self._rebuild_params()

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


class WorkflowEditor(ttk.Frame):
    def __init__(
        self,
        parent,
        workflows_dir: str = "workflows",
        steps_dir: str = "steps",
        on_save=None,
        get_steps_list=None,
        app=None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.workflows_dir = Path(workflows_dir)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.steps_dir = Path(steps_dir)
        self.steps_dir.mkdir(parents=True, exist_ok=True)
        self.on_save = on_save
        self.get_steps_list = get_steps_list or (lambda: [])
        self.app = app
        self.current_path: str | None = None
        self.action_cards: list[WorkflowActionCard] = []
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=5, pady=5)

        ttk.Label(top, text="Nome:").pack(side="left", padx=(0, 5))
        self.name_var = StringVar()
        ttk.Entry(top, textvariable=self.name_var, width=20).pack(side="left", padx=(0, 15))

        self.mode_var = StringVar(value="steps")
        ttk.Radiobutton(top, text="A partir de steps", variable=self.mode_var, value="steps", command=self._toggle_mode).pack(side="left", padx=5)
        ttk.Radiobutton(top, text="Editar actions manualmente", variable=self.mode_var, value="manual", command=self._toggle_mode).pack(side="left", padx=5)

        ttk.Button(top, text="Novo", command=self._new).pack(side="left", padx=2)
        ttk.Button(top, text="Salvar", command=self._save).pack(side="left", padx=2)
        ttk.Button(top, text="Carregar", command=self._load_selected).pack(side="left", padx=2)

        # Modo steps
        self.steps_frame = ttk.LabelFrame(self, text="Steps (clique + para adicionar, arraste para reordenar)")
        self.steps_listbox = ttk.Treeview(self.steps_frame, height=6, selectmode="extended", columns=("path",), show="tree")
        self.steps_listbox.column("#0", width=250)
        self.steps_listbox.pack(fill="x", padx=5, pady=5)
        sb = ttk.Frame(self.steps_frame)
        sb.pack(fill="x", padx=5, pady=2)
        ttk.Button(sb, text="+ Adicionar step", command=self._add_step_dialog).pack(side="left", padx=2)
        ttk.Button(sb, text="Remover", command=self._remove_selected_step).pack(side="left", padx=2)
        ttk.Button(sb, text="Subir", command=self._move_step_up).pack(side="left", padx=2)
        ttk.Button(sb, text="Descer", command=self._move_step_down).pack(side="left", padx=2)

        ttk.Label(self.steps_frame, text="URL (opcional):").pack(anchor="w", padx=5, pady=(2, 0))
        self.url_var = StringVar()
        ttk.Entry(self.steps_frame, textvariable=self.url_var, width=50).pack(fill="x", padx=5, pady=2)
        ttk.Label(self.steps_frame, text="Browser:").pack(anchor="w", padx=5, pady=(2, 0))
        self.browser_var = StringVar(value="chromium")
        ttk.Combobox(self.steps_frame, textvariable=self.browser_var, values=["chromium", "firefox", "webkit"], width=15).pack(anchor="w", padx=5, pady=2)

        # Modo manual
        self.manual_frame = ttk.LabelFrame(self, text="Actions do workflow")
        mf_top = ttk.Frame(self.manual_frame)
        mf_top.pack(fill="x", padx=5, pady=5)
        ttk.Label(mf_top, text="URL:").pack(side="left", padx=(0, 5))
        self.manual_url_var = StringVar(value="https://example.com")
        ttk.Entry(mf_top, textvariable=self.manual_url_var, width=45).pack(side="left", padx=(0, 15))
        ttk.Label(mf_top, text="Browser:").pack(side="left", padx=(0, 5))
        self.manual_browser_var = StringVar(value="chromium")
        ttk.Combobox(mf_top, textvariable=self.manual_browser_var, values=["chromium", "firefox", "webkit"], width=12).pack(side="left")
        self.manual_container = ttk.Frame(self.manual_frame)
        self.manual_container.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Button(self.manual_frame, text="+ Adicionar action", command=self._add_manual_action).pack(padx=5, pady=5)

        self._toggle_mode()

    def _toggle_mode(self):
        if self.mode_var.get() == "steps":
            self.steps_frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.manual_frame.pack_forget()
        else:
            self.steps_frame.pack_forget()
            self.manual_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def _add_step_dialog(self):
        steps = self.get_steps_list()
        if not steps:
            messagebox.showinfo("Steps", "Nenhum step em steps/. Crie steps primeiro.")
            return
        win = Toplevel(self)
        win.title("Adicionar step")
        win.geometry("350x280")
        lb = ttk.Treeview(win, height=10, selectmode="browse", columns=("path",), show="tree")
        lb.pack(fill="both", expand=True, padx=5, pady=5)
        for s in steps:
            lb.insert("", "end", text=Path(s).name, values=(s,))

        def on_ok():
            sel = lb.selection()
            if sel:
                path = lb.item(sel[0])["values"][0]
                self.steps_listbox.insert("", "end", text=Path(path).name, values=(path,))
            win.destroy()

        ttk.Button(win, text="Adicionar", command=on_ok).pack(pady=5)

    def _remove_selected_step(self):
        for sel in self.steps_listbox.selection():
            self.steps_listbox.delete(sel)

    def _move_step_up(self):
        sel = self.steps_listbox.selection()
        if not sel:
            return
        idx = self.steps_listbox.index(sel[0])
        if idx > 0:
            item = self.steps_listbox.item(sel[0])
            self.steps_listbox.delete(sel[0])
            self.steps_listbox.insert("", idx - 1, text=item["text"], values=item["values"])

    def _move_step_down(self):
        sel = self.steps_listbox.selection()
        if not sel:
            return
        idx = self.steps_listbox.index(sel[0])
        if idx < len(self.steps_in_workflow) - 1:
            item = self.steps_listbox.item(sel[0])
            self.steps_listbox.delete(sel[0])
            self.steps_listbox.insert("", idx + 1, text=item["text"], values=item["values"])

    def _add_manual_action(self, action_data: dict | None = None):
        data = action_data or {"name": "goto", "params": {"url": "https://example.com"}}
        card = WorkflowActionCard(
            self.manual_container,
            data,
            on_remove=lambda: self._remove_action_card(card),
            on_move=lambda direction: self._move_action_card(card, direction),
        )
        card.pack(fill="x", pady=3)
        self.action_cards.append(card)

    def _remove_action_card(self, card: WorkflowActionCard):
        if card in self.action_cards:
            self.action_cards.remove(card)
            card.destroy()

    def _move_action_card(self, card: WorkflowActionCard, direction: str):
        idx = self.action_cards.index(card)
        if direction == "up" and idx > 0:
            self.action_cards[idx], self.action_cards[idx - 1] = self.action_cards[idx - 1], self.action_cards[idx]
        elif direction == "down" and idx < len(self.action_cards) - 1:
            self.action_cards[idx], self.action_cards[idx + 1] = self.action_cards[idx + 1], self.action_cards[idx]
        for c in self.action_cards:
            c.pack_forget()
        for c in self.action_cards:
            c.pack(fill="x", pady=3)

    def _get_selected_workflow(self) -> str | None:
        if self.app and hasattr(self.app, "get_selected_workflow"):
            return self.app.get_selected_workflow()
        return None

    def _load_selected(self):
        path = self._get_selected_workflow()
        if path:
            self._load(path)
        else:
            messagebox.showinfo("Carregar", "Selecione um workflow na lista à esquerda.")

    def _load(self, path: str):
        p = Path(path)
        if not p.exists():
            messagebox.showerror("Erro", f"Arquivo não encontrado: {path}")
            return
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            self.current_path = path
            self.name_var.set(p.stem)
            if self.mode_var.get() == "manual":
                actions = data.get("browsers", [{}])[0].get("pages", [{}])[0].get("actions", [])
                for card in self.action_cards[:]:
                    card.destroy()
                self.action_cards.clear()
                for a in actions:
                    self._add_manual_action(a)
            else:
                messagebox.showinfo("Carregar", "Workflow carregado. No modo 'steps', carregue criando a partir de steps.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _new(self):
        self.current_path = None
        self.name_var.set("")
        self.steps_listbox.delete(*self.steps_listbox.get_children())
        self.url_var.set("")
        self.browser_var.set("chromium")
        for card in self.action_cards[:]:
            card.destroy()
        self.action_cards.clear()
        if self.mode_var.get() == "manual":
            self._add_manual_action()

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Salvar", "Informe o nome.")
            return
        try:
            if self.mode_var.get() == "steps":
                steps_paths = [self.steps_listbox.item(c)["values"][0] for c in self.steps_listbox.get_children()]
                if not steps_paths:
                    messagebox.showwarning("Salvar", "Adicione pelo menos um step.")
                    return
                workflow = MakeWorkflowByStep.make(
                    steps_paths,
                    url=self.url_var.get().strip() or None,
                    browser_type=self.browser_var.get(),
                    output_name=name,
                )
            else:
                actions = [c.get_data() for c in self.action_cards]
                if not actions:
                    messagebox.showwarning("Salvar", "Adicione pelo menos uma action.")
                    return
                url = self.manual_url_var.get().strip() or "about:blank"
                page = Page(url=url, actions=[Action(**a) for a in actions])
                browser = Browser(btype=BrowserType(self.manual_browser_var.get()), pages=[page])
                workflow = Workflow(browsers=[browser])
                path = self.workflows_dir / f"{name}.json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(workflow.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
            self.current_path = str(self.workflows_dir / f"{name}.json")
            messagebox.showinfo("Salvar", f"Workflow salvo em {self.current_path}")
            if self.on_save:
                self.on_save()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def get_workflow(self) -> Workflow | None:
        try:
            if self.mode_var.get() == "steps":
                steps_paths = [self.steps_listbox.item(c)["values"][0] for c in self.steps_listbox.get_children()]
                if not steps_paths:
                    return None
                return MakeWorkflowByStep.make(
                    steps_paths,
                    url=self.url_var.get().strip() or None,
                    browser_type=self.browser_var.get(),
                    output_name="temp",
                    save=False,
                )
            else:
                actions = [c.get_data() for c in self.action_cards]
                if not actions:
                    return None
                url = self.manual_url_var.get().strip() or "about:blank"
                page = Page(url=url, actions=[Action(**a) for a in actions])
                browser = Browser(btype=BrowserType(self.manual_browser_var.get()), pages=[page])
                return Workflow(browsers=[browser])
        except Exception:
            return None
