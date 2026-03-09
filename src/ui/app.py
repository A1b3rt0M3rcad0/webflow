"""
Janela principal da UI WebFlow.
"""
import json
import queue
import os
from pathlib import Path
from tkinter import ttk, messagebox, Text, END

from src.ui.runner import run_workflow
from src.ui.step_editor import StepEditor
from src.ui.workflow_editor import WorkflowEditor


def safe_find_steps() -> list[str]:
    try:
        from src.utils.steps_finder import StepsFinder
        Path(StepsFinder.steps_directory).mkdir(parents=True, exist_ok=True)
        return StepsFinder.find()
    except (FileNotFoundError, OSError):
        Path("steps").mkdir(parents=True, exist_ok=True)
        return []


def safe_find_workflows() -> list[str]:
    try:
        from src.utils.workflows_finder import WorkflowsFinder
        Path(WorkflowsFinder.workflows_directory).mkdir(parents=True, exist_ok=True)
        return sorted(WorkflowsFinder.find())
    except (FileNotFoundError, OSError):
        Path("workflows").mkdir(parents=True, exist_ok=True)
        return []


class App(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.log_queue: queue.Queue = queue.Queue()
        self._build_ui()
        self._refresh_lists()
        self._poll_log()

    def _build_ui(self):
        # Painel esquerdo: listas
        left = ttk.Frame(self, width=220)
        left.pack(side="left", fill="y", padx=5, pady=5)
        left.pack_propagate(False)

        ttk.Label(left, text="Steps").pack(anchor="w")
        self.steps_listbox = ttk.Treeview(left, height=8, selectmode="browse", columns=("path",), show="tree")
        self.steps_listbox.column("#0", width=180)
        self.steps_listbox.pack(fill="both", expand=True, pady=2)
        self.steps_listbox.bind("<<TreeviewSelect>>", self._on_step_select)
        self.steps_listbox.bind("<Double-1>", lambda e: self._load_step())

        ttk.Label(left, text="Workflows").pack(anchor="w", pady=(10, 0))
        self.workflows_listbox = ttk.Treeview(left, height=8, selectmode="browse", columns=("path",), show="tree")
        self.workflows_listbox.column("#0", width=180)
        self.workflows_listbox.pack(fill="both", expand=True, pady=2)
        self.workflows_listbox.bind("<<TreeviewSelect>>", self._on_workflow_select)
        self.workflows_listbox.bind("<Double-1>", lambda e: self._load_workflow())

        ttk.Button(left, text="Atualizar listas", command=self._refresh_lists).pack(pady=5)

        # Painel central: notebook (Steps / Workflows)
        center = ttk.Frame(self)
        center.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(center)
        self.notebook.pack(fill="both", expand=True)

        self.step_editor = StepEditor(center, on_save=self._refresh_lists, app=self)
        self.notebook.add(self.step_editor, text="Step")

        self.workflow_editor = WorkflowEditor(
            center,
            on_save=self._refresh_lists,
            get_steps_list=safe_find_steps,
            app=self,
        )
        self.notebook.add(self.workflow_editor, text="Workflow")

        # Botões de ação (visíveis em ambas as abas)
        btn_frame = ttk.Frame(center)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="Testar", command=self._run_current).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Salvar", command=self._save_current).pack(side="left", padx=2)

        # Painel inferior: log
        log_frame = ttk.LabelFrame(self, text="Log / Saída")
        log_frame.pack(side="bottom", fill="both", expand=True, padx=5, pady=5)
        self.log_text = Text(log_frame, height=10, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)
        ttk.Button(log_frame, text="Limpar log", command=self._clear_log).pack(pady=2)

    def _refresh_lists(self):
        for c in self.steps_listbox.get_children():
            self.steps_listbox.delete(c)
        for p in safe_find_steps():
            self.steps_listbox.insert("", "end", text=Path(p).name, values=(p,))

        for c in self.workflows_listbox.get_children():
            self.workflows_listbox.delete(c)
        for p in safe_find_workflows():
            self.workflows_listbox.insert("", "end", text=Path(p).name, values=(p,))

    def get_selected_step(self) -> str | None:
        sel = self.steps_listbox.selection()
        if sel:
            return self.steps_listbox.item(sel[0])["values"][0]
        return None

    def get_selected_workflow(self) -> str | None:
        sel = self.workflows_listbox.selection()
        if sel:
            return self.workflows_listbox.item(sel[0])["values"][0]
        return None

    def _on_step_select(self, event):
        pass

    def _on_workflow_select(self, event):
        pass

    def _load_step(self):
        path = self.get_selected_step()
        if path:
            self.notebook.select(0)
            self.step_editor._load(path)

    def _load_workflow(self):
        path = self.get_selected_workflow()
        if path:
            self.notebook.select(1)
            self.workflow_editor._load(path)

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", END)
        self.log_text.configure(state="disabled")

    def _log(self, text: str):
        self.log_text.configure(state="normal")
        self.log_text.insert(END, text)
        self.log_text.see(END)
        self.log_text.configure(state="disabled")

    def _poll_log(self):
        try:
            while True:
                text = self.log_queue.get_nowait()
                self._log(text)
        except queue.Empty:
            pass
        self.after(100, self._poll_log)

    def _run_current(self):
        """Testa o step ou workflow da aba atual."""
        if self.notebook.index(self.notebook.select()) == 0:
            workflow = self.step_editor.get_workflow_for_test()
        else:
            workflow = self.workflow_editor.get_workflow()
        if workflow is None:
            messagebox.showerror("Testar", "Step ou workflow inválido. Adicione actions ou steps.")
            return
        self._log("\n--- Iniciando teste ---\n")
        run_workflow(
            workflow,
            self.log_queue,
            on_done=lambda ok, err: self.after(0, lambda: self._on_run_done(ok, err)),
        )

    def _save_current(self):
        """Salva o step ou workflow da aba atual."""
        if self.notebook.index(self.notebook.select()) == 0:
            self.step_editor._save()
        else:
            self.workflow_editor._save()

    def _on_run_done(self, ok: bool, err: str | None):
        if ok:
            self._log("\n--- Execução concluída ---\n")
        else:
            self._log(f"\n--- Erro: {err} ---\n")
