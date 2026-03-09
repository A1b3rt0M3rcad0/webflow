import json
import queue
import os
from pathlib import Path
from tkinter import ttk, messagebox, Toplevel, Text, END

from src.ui.runner import run_workflow
from src.ui.step_editor import StepEditor
from src.ui.workflow_editor import WorkflowEditor
from src.utils.template_utils import extract_template_vars, substitute_templates


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


def _open_run_console(parent, title: str):
    win = Toplevel(parent)
    win.title(title)
    win.geometry("900x550")
    win.minsize(500, 350)
    q = queue.Queue()

    frame = ttk.Frame(win, padding=8)
    frame.pack(fill="both", expand=True)
    # Terminal: fundo escuro, fonte monoespaçada
    text = Text(
        frame,
        wrap="word",
        state="disabled",
        font=("Consolas", 11),
        bg="#0c0c0c",
        fg="#cccccc",
        insertbackground="#cccccc",
        selectbackground="#264f78",
    )
    text.pack(fill="both", expand=True)
    scroll = ttk.Scrollbar(frame, command=text.yview)
    scroll.pack(side="right", fill="y")
    text.configure(yscrollcommand=scroll.set)
    ttk.Button(frame, text="Fechar", command=win.destroy).pack(pady=6)

    def poll():
        try:
            while True:
                s = q.get_nowait()
                text.configure(state="normal")
                text.insert(END, s)
                text.see(END)
                text.configure(state="disabled")
        except queue.Empty:
            pass
        if win.winfo_exists():
            win.after(50, poll)

    win.after(50, poll)
    return q


def _show_template_dialog(parent, vars_list: list[str], title: str = "Preencher variáveis") -> dict[str, str] | None:
    """
    Mostra diálogo para preencher valores de {{var}}.
    Retorna dict com os valores ou None se cancelado.
    """
    result: dict[str, str] | None = None
    entries: dict[str, ttk.Entry] = {}

    win = Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.grab_set()
    win.resizable(False, False)

    f = ttk.Frame(win, padding=15)
    f.pack(fill="x")
    ttk.Label(f, text="Preencha os valores dos templates antes de executar:").pack(anchor="w", pady=(0, 10))
    for var in sorted(vars_list):
        row = ttk.Frame(f)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text=f"{{{{{var}}}}}:", width=20, anchor="w").pack(side="left", padx=(0, 8))
        e = ttk.Entry(row, width=35)
        e.pack(side="left", fill="x", expand=True)
        entries[var] = e

    def on_ok():
        nonlocal result
        result = {var: e.get().strip() for var, e in entries.items()}
        win.destroy()

    def on_cancel():
        win.destroy()

    btn_f = ttk.Frame(f)
    btn_f.pack(fill="x", pady=(15, 0))
    ttk.Button(btn_f, text="Executar", command=on_ok).pack(side="left", padx=2)
    ttk.Button(btn_f, text="Cancelar", command=on_cancel).pack(side="left", padx=2)

    win.geometry("450x200")
    parent.wait_window(win)
    return result


class App(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build_ui()
        self._refresh_lists()

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

        ttk.Button(left, text="Deletar workflow", command=self._delete_selected_workflow).pack(fill="x", pady=2)

        ttk.Button(left, text="Atualizar listas", command=self._refresh_lists).pack(pady=5)

        # Painel central: notebook (Steps / Workflows)
        center = ttk.Frame(self)
        center.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(center)
        self.notebook.pack(fill="both", expand=True)

        self.step_editor = StepEditor(center, on_save=self._refresh_lists, on_test=self._run_step_test, app=self)
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
        ttk.Button(btn_frame, text="Salvar", command=self._save_current).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Executar workflow selecionado", command=self._run_selected_workflow).pack(side="left", padx=2)

    def _refresh_lists(self):
        for c in self.steps_listbox.get_children():
            self.steps_listbox.delete(c)
        for p in safe_find_steps():
            path_abs = str(Path(p).resolve())
            self.steps_listbox.insert("", "end", text=Path(p).name, values=(path_abs,))

        for c in self.workflows_listbox.get_children():
            self.workflows_listbox.delete(c)
        for p in safe_find_workflows():
            path_abs = str(Path(p).resolve())
            self.workflows_listbox.insert("", "end", text=Path(p).name, values=(path_abs,))

    def get_selected_step(self) -> str | None:
        sel = self.steps_listbox.selection()
        if sel:
            return self.steps_listbox.item(sel[0])["values"][0]
        return None

    def get_selected_workflow(self) -> str | None:
        sel = self.workflows_listbox.selection()
        if not sel:
            return None
        item = self.workflows_listbox.item(sel[0])
        vals = item.get("values") or ()
        if vals:
            return vals[0]
        # Fallback: reconstruir path pelo nome (coluna #0)
        name = item.get("text") or ""
        if name:
            for p in safe_find_workflows():
                if Path(p).name == name:
                    return str(Path(p).resolve())
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

    def _delete_selected_workflow(self):
        path = self.get_selected_workflow()
        if not path:
            messagebox.showinfo("Deletar", "Selecione um workflow na lista à esquerda.")
            return
        path_obj = Path(path)
        if not path_obj.exists():
            messagebox.showerror("Deletar", f"Arquivo não encontrado: {path}")
            self._refresh_lists()
            return
        if not messagebox.askyesno("Deletar workflow", f"Deletar o workflow \"{path_obj.name}\"?\n\nO arquivo será removido permanentemente."):
            return
        try:
            path_obj.unlink()
            self._refresh_lists()
            messagebox.showinfo("Deletar", f"Workflow \"{path_obj.name}\" removido.")
        except OSError as e:
            messagebox.showerror("Deletar", f"Não foi possível remover: {e}")

    def _run_step_test(self):
        """Testa o step da aba Step. Abre console estilo terminal."""
        workflow = self.step_editor.get_workflow_for_test()
        if workflow is None:
            messagebox.showerror("Testar", "Step inválido. Adicione actions.")
            return
        workflow = self._resolve_templates(workflow, "Step (teste)")
        if workflow is None:
            return
        name = self.step_editor.get_current_name() or "Step (teste)"
        log_queue = _open_run_console(self.winfo_toplevel(), f"Executando: {name}")
        log_queue.put("\n--- Iniciando teste ---\n")
        run_workflow(
            workflow,
            log_queue,
            on_done=lambda ok, err: self._console_done(log_queue, ok, err),
        )

    def _run_selected_workflow(self):
        path = self.get_selected_workflow()
        if not path:
            messagebox.showinfo("Executar", "Selecione um workflow na lista à esquerda.")
            return
        try:
            from src.utils.workflow_runner import load_workflow_from_json
            path_resolved = str(Path(path).resolve())
            workflow = load_workflow_from_json(path_resolved)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        name = Path(path).name
        workflow = self._resolve_templates(workflow, name)
        if workflow is None:
            return
        log_queue = _open_run_console(self.winfo_toplevel(), f"Executando: {name}")
        log_queue.put(f"\n--- Executando {name} ---\n")
        run_workflow(
            workflow,
            log_queue,
            on_done=lambda ok, err: self._console_done(log_queue, ok, err),
        )

    def _save_current(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self.step_editor._save()
        else:
            self.workflow_editor._save()

    def _resolve_templates(self, workflow, name: str):
        """Se o workflow tem {{var}}, mostra diálogo para preencher. Retorna workflow com valores ou None se cancelado."""
        vars_list = extract_template_vars(workflow)
        if not vars_list:
            return workflow
        values = _show_template_dialog(self.winfo_toplevel(), list(vars_list), f"Preencher variáveis - {name}")
        if values is None:
            return None
        return substitute_templates(workflow, values)

    def _console_done(self, log_queue: queue.Queue, ok: bool, err: str | None):
        if ok:
            log_queue.put("\n--- Execução concluída ---\n")
        else:
            log_queue.put(f"\n--- Erro: {err} ---\n")

