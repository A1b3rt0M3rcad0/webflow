import json
from pathlib import Path
from tkinter import ttk, messagebox, StringVar, Canvas, Toplevel

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
        new_name = self.type_var.get()
        old_name = self.action_data.get("name", "goto")
        self.action_data["name"] = new_name
        
        # Se mudou para IF, garantir que params tenha estrutura correta
        if new_name == "if":
            if "params" not in self.action_data or not self.action_data["params"]:
                self.action_data["params"] = {"condition": {"type": "equals"}, "then": [], "else_": []}
        else:
            if old_name == "if":
                # Se estava em IF e mudou para outro tipo, limpar params
                self.action_data["params"] = {}
        
        self._rebuild_params()
        # Notificar mudança de tipo - isso pode recriar o card se necessário
        self.on_change("type")

    def _rebuild_params(self):
        for w in self.params_frame.winfo_children():
            w.destroy()
        name = self.type_var.get()
        
        # Se for IF, armazenar referência ao card no params_frame (mesmo que seja ActionCard comum)
        # IMPORTANTE: Armazenar ANTES de construir o formulário
        if name == "if":
            print(f"[DEBUG ActionCard._rebuild_params] Tipo é IF, self é: {type(self).__name__}")
            # Armazenar referência sempre que tipo for "if", independente do tipo do card
            self.params_frame._if_action_card_ref = self
            print(f"[DEBUG ActionCard._rebuild_params] Armazenando referência ao card no params_frame: {self.params_frame}")
            print(f"[DEBUG] Referência armazenada: {self.params_frame._if_action_card_ref}")
            
            # Se for ActionCard comum e tipo for "if", adicionar métodos dinamicamente
            if not isinstance(self, IfActionCard):
                print(f"[DEBUG] Adicionando métodos _edit_then e _edit_else dinamicamente ao ActionCard")
                if not hasattr(self, '_edit_then'):
                    self._edit_then = self._create_edit_then_method()
                if not hasattr(self, '_edit_else'):
                    self._edit_else = self._create_edit_else_method()
        
        form_frame, self.vars_dict = build_action_params_form(
            self.params_frame, name, self.action_data.get("params")
        )
        form_frame.pack(fill="x")
        
        # Se for IF, conectar os botões após construir o formulário
        if name == "if":
            if isinstance(self, IfActionCard):
                # Se for IfActionCard, usar método próprio
                self.after_idle(self._connect_buttons)
            else:
                # Se for ActionCard comum, conectar diretamente através do vars_dict
                self.after_idle(lambda: self._connect_if_buttons())

    def get_data(self) -> dict:
        name = self.type_var.get()
        params = get_params_from_form(self.vars_dict, name) or {}
        
        # Se for ação IF, incluir then e else_ do action_data (que são salvos pelo IfActionsEditor)
        if name == "if":
            # Preservar then e else_ que foram salvos no action_data
            action_params = self.action_data.get("params", {})
            if "then" in action_params:
                params["then"] = action_params["then"]
                print(f"[DEBUG ActionCard.get_data] Incluindo then: {len(params['then'])} ações")
            else:
                params["then"] = []
                print(f"[DEBUG ActionCard.get_data] then não encontrado, usando []")
            
            if "else_" in action_params:
                params["else_"] = action_params["else_"]
                print(f"[DEBUG ActionCard.get_data] Incluindo else_: {len(params['else_'])} ações")
            else:
                params["else_"] = []
                print(f"[DEBUG ActionCard.get_data] else_ não encontrado, usando []")
            
            print(f"[DEBUG ActionCard.get_data] Params finais para IF: then={len(params.get('then', []))}, else_={len(params.get('else_', []))}")
        
        return {"name": name, "params": params}
    
    def _create_edit_then_method(self):
        """Cria método _edit_then dinamicamente para ActionCard quando tipo é 'if'"""
        # IfActionsEditor está definido mais abaixo no mesmo arquivo
        def _edit_then():
            """Abre editor para bloco THEN"""
            print(f"[DEBUG ActionCard._edit_then] CHAMADO!")
            print(f"[DEBUG] action_data antes de abrir editor: {self.action_data}")
            print(f"[DEBUG] ID do action_data: {id(self.action_data)}")
            print(f"[DEBUG] params antes: {self.action_data.get('params', {})}")
            try:
                parent = self.winfo_toplevel()
                print(f"[DEBUG] Parent window: {parent}")
                print(f"[DEBUG] Criando IfActionsEditor com action_data (referência)...")
                # Passar self.action_data diretamente (é uma referência ao dict)
                editor = IfActionsEditor(parent, self.action_data, on_save=self._on_if_actions_saved)
                print(f"[DEBUG] IfActionsEditor criado: {editor}")
                print(f"[DEBUG] action_data no editor: {editor.action_data}")
                print(f"[DEBUG] IDs são iguais? {id(self.action_data) == id(editor.action_data)}")
                editor.focus_set()
                editor.grab_set()
                print(f"[DEBUG] Editor configurado, aguardando...")
                editor.wait_window()  # Aguardar até a janela ser fechada
                print(f"[DEBUG] Editor fechado")
                print(f"[DEBUG] action_data após fechar editor: {self.action_data}")
                print(f"[DEBUG] params após fechar: {self.action_data.get('params', {})}")
            except Exception as e:
                print(f"[DEBUG] ERRO ao abrir editor THEN: {e}")
                import traceback
                traceback.print_exc()
                from tkinter import messagebox
                messagebox.showerror("Erro", f"Erro ao abrir editor THEN: {e}")
        return _edit_then
    
    def _create_edit_else_method(self):
        """Cria método _edit_else dinamicamente para ActionCard quando tipo é 'if'"""
        # IfActionsEditor está definido mais abaixo no mesmo arquivo
        def _edit_else():
            """Abre editor para bloco ELSE"""
            print(f"[DEBUG ActionCard._edit_else] CHAMADO!")
            print(f"[DEBUG] action_data: {self.action_data}")
            try:
                parent = self.winfo_toplevel()
                print(f"[DEBUG] Parent window: {parent}")
                print(f"[DEBUG] Criando IfActionsEditor...")
                # IfActionsEditor está definido no mesmo arquivo, então está disponível
                editor = IfActionsEditor(parent, self.action_data, on_save=self._on_if_actions_saved)
                print(f"[DEBUG] IfActionsEditor criado: {editor}")
                editor.focus_set()
                editor.grab_set()
                print(f"[DEBUG] Editor configurado, aguardando...")
                editor.wait_window()  # Aguardar até a janela ser fechada
                print(f"[DEBUG] Editor fechado")
            except Exception as e:
                print(f"[DEBUG] ERRO ao abrir editor ELSE: {e}")
                import traceback
                traceback.print_exc()
                from tkinter import messagebox
                messagebox.showerror("Erro", f"Erro ao abrir editor ELSE: {e}")
        return _edit_else
    
    def _on_if_actions_saved(self):
        """Callback quando ações IF são salvas (para ActionCard comum)"""
        print(f"[DEBUG ActionCard._on_if_actions_saved] Callback chamado")
        print(f"[DEBUG] action_data do card: {self.action_data}")
        print(f"[DEBUG] params no action_data: {self.action_data.get('params', {})}")
        
        # Verificar se os dados foram realmente salvos
        params = self.action_data.get("params", {})
        then_count = len(params.get("then", []))
        else_count = len(params.get("else_", []))
        total_count = then_count + else_count
        
        print(f"[DEBUG] Contadores: THEN={then_count}, ELSE={else_count}, TOTAL={total_count}")
        
        # Atualizar texto do botão se existir
        if hasattr(self, 'vars_dict') and self.vars_dict:
            if "_edit_actions_button" in self.vars_dict:
                edit_btn, _ = self.vars_dict["_edit_actions_button"]
                if edit_btn:
                    edit_btn.config(text=f"✏️ Editar Actions ({total_count} ação(ões) total)")
                    print(f"[DEBUG] Botão atualizado com novo texto")
            else:
                print(f"[DEBUG] Botão _edit_actions_button não encontrado no vars_dict")
        else:
            print(f"[DEBUG] vars_dict não existe ou está vazio")
        
        # Notificar mudança
        if self.on_change:
            print(f"[DEBUG] Chamando on_change('actions_updated')")
            self.on_change("actions_updated")
    
    def _connect_if_buttons(self):
        """Conecta o botão do formulário IF quando ActionCard comum"""
        if not hasattr(self, 'vars_dict') or not self.vars_dict:
            return
        
        # Buscar botão no vars_dict
        try:
            if "_edit_actions_button" in self.vars_dict:
                edit_btn, _ = self.vars_dict["_edit_actions_button"]
                if edit_btn and hasattr(self, '_edit_then'):
                    edit_btn.config(command=self._edit_then)
                    params = self.action_data.get("params", {})
                    then_count = len(params.get("then", []))
                    else_count = len(params.get("else_", []))
                    total_count = then_count + else_count
                    edit_btn.config(text=f"✏️ Editar Actions ({total_count} ação(ões) total)")
                    print(f"[DEBUG ActionCard._connect_if_buttons] Botão Editar Actions conectado")
        except Exception as e:
            print(f"[DEBUG] ERRO ao conectar botão IF: {e}")
            import traceback
            traceback.print_exc()


class IfActionsEditor(Toplevel):
    """Janela modal para editar ações dos blocos THEN e ELSE do IF"""
    
    def __init__(self, parent, action_data: dict, on_save=None):
        super().__init__(parent)
        self.action_data = action_data
        self.on_save = on_save
        self.then_cards: list[ActionCard] = []
        self.else_cards: list[ActionCard] = []
        
        self.title("Editar ações IF - THEN / ELSE")
        self.geometry("900x700")
        self.minsize(600, 400)
        
        self._build_ui()
        self._load_actions()
    
    def _build_ui(self):
        # Container principal com notebook para THEN/ELSE
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Aba THEN
        then_frame = ttk.Frame(notebook)
        notebook.add(then_frame, text="THEN (se verdadeiro)")
        self._build_actions_frame(then_frame, "then")
        
        # Aba ELSE
        else_frame = ttk.Frame(notebook)
        notebook.add(else_frame, text="ELSE (se falso)")
        self._build_actions_frame(else_frame, "else_")
        
        # Botões de ação
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Salvar", command=self._save).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=2)
    
    def _build_actions_frame(self, parent: ttk.Frame, block_name: str):
        """Constrói o frame de ações para um bloco (THEN ou ELSE)"""
        # Botão adicionar ação no topo (sempre visível)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=5, pady=5)
        add_btn = ttk.Button(btn_frame, text=f"+ Adicionar ação em {block_name.upper()}", 
                            command=lambda: self._add_action(cards_container, block_name))
        add_btn.pack(side="left", padx=2)
        
        # Container com scroll abaixo do botão
        scroll_container = ttk.Frame(parent)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = Canvas(scroll_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, command=canvas.yview)
        cards_container = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        
        def _update_scroll_region(*_):
            bbox = canvas.bbox("all")
            if not bbox:
                return
            x1, y1, x2, y2 = bbox
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            content_h = y2 - y1
            scroll_h = max(ch, content_h)
            scroll_w = max(cw, x2 - x1)
            canvas.configure(scrollregion=(0, 0, scroll_w, scroll_h))
            if content_h <= ch:
                canvas.yview_moveto(0)
        
        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
            canvas.after_idle(_update_scroll_region)
        
        cards_container.bind("<Configure>", lambda e: canvas.after_idle(_update_scroll_region))
        canvas.bind("<Configure>", _on_canvas_configure)
        
        canvas_window = canvas.create_window((0, 0), window=cards_container, anchor="nw")
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Armazenar referências
        if block_name == "then":
            self.then_cards_container = cards_container
            self.then_canvas = canvas
            self.then_add_btn = add_btn
        else:
            self.else_cards_container = cards_container
            self.else_canvas = canvas
            self.else_add_btn = add_btn
    
    def _add_action(self, container: ttk.Frame, block_name: str, action_data: dict | None = None):
        """Adiciona uma ação ao bloco especificado"""
        data = action_data or {"name": "goto", "params": {"url": "https://example.com"}}
        card = ActionCard(
            container,
            data,
            on_remove=lambda: self._remove_card(card, block_name),
            on_change=lambda _: None,
        )
        card.pack(fill="x", pady=3)
        
        if block_name == "then":
            self.then_cards.append(card)
        else:
            self.else_cards.append(card)
        
        self._update_card_order(block_name)
        self._update_add_button_position(block_name)
    
    def _update_add_button_position(self, block_name: str):
        """Atualiza a posição do botão de adicionar dentro do container"""
        container = self.then_cards_container if block_name == "then" else self.else_cards_container
        
        # Remover botão antigo se existir
        for widget in container.winfo_children():
            if isinstance(widget, ttk.Button) and "+" in str(widget.cget("text")):
                widget.destroy()
        
        # Adicionar botão no final da lista
        add_btn_inner = ttk.Button(
            container,
            text=f"+ Adicionar ação",
            command=lambda: self._add_action(container, block_name)
        )
        add_btn_inner.pack(fill="x", pady=5, padx=5)
    
    def _remove_card(self, card: ActionCard, block_name: str):
        """Remove uma ação do bloco especificado"""
        if block_name == "then":
            if card in self.then_cards:
                self.then_cards.remove(card)
        else:
            if card in self.else_cards:
                self.else_cards.remove(card)
        card.destroy()
        self._update_card_order(block_name)
        self._update_add_button_position(block_name)
    
    def _update_card_order(self, block_name: str):
        """Atualiza a ordem dos cards"""
        cards = self.then_cards if block_name == "then" else self.else_cards
        for i, card in enumerate(cards):
            card.on_change = lambda direction, c=card, bn=block_name: self._move_card(c, direction, bn)
    
    def _move_card(self, card: ActionCard, direction: str, block_name: str):
        """Move um card para cima ou para baixo"""
        cards = self.then_cards if block_name == "then" else self.else_cards
        idx = cards.index(card)
        if direction == "up" and idx > 0:
            cards[idx], cards[idx - 1] = cards[idx - 1], cards[idx]
        elif direction == "down" and idx < len(cards) - 1:
            cards[idx], cards[idx + 1] = cards[idx + 1], cards[idx]
        self._reorder_cards_ui(block_name)
    
    def _reorder_cards_ui(self, block_name: str):
        """Reordena os cards na UI"""
        cards = self.then_cards if block_name == "then" else self.else_cards
        container = self.then_cards_container if block_name == "then" else self.else_cards_container
        for card in cards:
            card.pack_forget()
        for card in cards:
            card.pack(fill="x", pady=3)
    
    def _load_actions(self):
        """Carrega ações existentes dos blocos THEN e ELSE"""
        params = self.action_data.get("params", {})
        then_actions = params.get("then", [])
        else_actions = params.get("else_", [])
        
        for action in then_actions:
            self._add_action(self.then_cards_container, "then", action)
        for action in else_actions:
            self._add_action(self.else_cards_container, "else_", action)
        
        # Adicionar botões após carregar
        self._update_add_button_position("then")
        self._update_add_button_position("else_")
    
    def _save(self):
        """Salva as ações de volta no action_data"""
        print(f"[DEBUG IfActionsEditor._save] Iniciando salvamento")
        print(f"[DEBUG] action_data ID: {id(self.action_data)}")
        print(f"[DEBUG] action_data antes: {self.action_data}")
        print(f"[DEBUG] Número de cards THEN: {len(self.then_cards)}")
        print(f"[DEBUG] Número de cards ELSE: {len(self.else_cards)}")
        
        # Coletar dados de cada card
        then_actions = []
        for i, card in enumerate(self.then_cards):
            card_data = card.get_data()
            then_actions.append(card_data)
            print(f"[DEBUG] Card THEN {i}: {card_data}")
        
        else_actions = []
        for i, card in enumerate(self.else_cards):
            card_data = card.get_data()
            else_actions.append(card_data)
            print(f"[DEBUG] Card ELSE {i}: {card_data}")
        
        print(f"[DEBUG] Ações THEN coletadas ({len(then_actions)}): {then_actions}")
        print(f"[DEBUG] Ações ELSE coletadas ({len(else_actions)}): {else_actions}")
        
        # Garantir que params existe e é modificado diretamente
        if "params" not in self.action_data:
            self.action_data["params"] = {}
            print(f"[DEBUG] Criado params vazio")
        else:
            print(f"[DEBUG] params já existe: {self.action_data['params']}")
        
        # Modificar diretamente no action_data (que é uma referência ao dict original)
        self.action_data["params"]["then"] = then_actions
        self.action_data["params"]["else_"] = else_actions
        
        print(f"[DEBUG] action_data após salvar: {self.action_data}")
        print(f"[DEBUG] params['then']: {self.action_data.get('params', {}).get('then', [])}")
        print(f"[DEBUG] params['else_']: {self.action_data.get('params', {}).get('else_', [])}")
        print(f"[DEBUG] Verificando se params foi atualizado: {self.action_data.get('params', {})}")
        
        # Verificar se realmente foi modificado
        if len(self.action_data.get("params", {}).get("then", [])) != len(then_actions):
            print(f"[ERROR] THEN não foi salvo corretamente! Esperado: {len(then_actions)}, Encontrado: {len(self.action_data.get('params', {}).get('then', []))}")
        if len(self.action_data.get("params", {}).get("else_", [])) != len(else_actions):
            print(f"[ERROR] ELSE não foi salvo corretamente! Esperado: {len(else_actions)}, Encontrado: {len(self.action_data.get('params', {}).get('else_', []))}")
        
        # Chamar callback se existir
        if self.on_save:
            print(f"[DEBUG] Chamando callback on_save")
            try:
                self.on_save()
                print(f"[DEBUG] Callback on_save executado com sucesso")
            except Exception as e:
                print(f"[DEBUG] ERRO ao executar callback on_save: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[DEBUG] Nenhum callback on_save definido")
        
        print(f"[DEBUG] Fechando editor")
        self.destroy()


class IfActionCard(ActionCard):
    """Card especializado para ação IF com botões para editar THEN/ELSE"""
    
    def _build(self):
        print(f"[DEBUG IfActionCard._build] Iniciando build do IfActionCard")
        # Chamar build do pai primeiro
        super()._build()
        print(f"[DEBUG IfActionCard._build] Build do pai concluído")
        print(f"[DEBUG] vars_dict após build: {hasattr(self, 'vars_dict')}")
        if hasattr(self, 'vars_dict'):
            print(f"[DEBUG] Chaves no vars_dict: {list(self.vars_dict.keys())}")
        # Os botões já estão no formulário, só precisamos conectá-los
        # Tentar conectar imediatamente e também usar after_idle como fallback
        self._connect_buttons()
        self.after_idle(self._connect_buttons)
        self.after(200, self._connect_buttons)  # Tentar novamente após 200ms
    
    def _rebuild_params(self):
        """Sobrescreve para garantir que os botões sejam reconectados após rebuild"""
        print(f"[DEBUG IfActionCard._rebuild_params] Chamando super()._rebuild_params()")
        print(f"[DEBUG] self é: {self}, tipo: {type(self).__name__}")
        print(f"[DEBUG] params_frame: {self.params_frame}")
        
        # IMPORTANTE: Armazenar referência ANTES de chamar super() para garantir que está disponível
        self.params_frame._if_action_card_ref = self
        print(f"[DEBUG IfActionCard._rebuild_params] Referência armazenada diretamente: {self.params_frame._if_action_card_ref}")
        print(f"[DEBUG] Verificando se foi armazenada: {hasattr(self.params_frame, '_if_action_card_ref')}")
        
        # Chamar método do pai
        super()._rebuild_params()
        print(f"[DEBUG IfActionCard._rebuild_params] Após super()._rebuild_params()")
        print(f"[DEBUG] params_frame tem _if_action_card_ref: {hasattr(self.params_frame, '_if_action_card_ref')}")
        if hasattr(self.params_frame, '_if_action_card_ref'):
            print(f"[DEBUG] Referência ainda presente: {self.params_frame._if_action_card_ref}")
        # Reconectar botões após rebuild - usar after_idle para garantir que está pronto
        self.after_idle(self._connect_buttons)
    
    def _connect_buttons(self):
        """Conecta os botões do formulário às funções de edição"""
        print(f"[DEBUG IfActionCard._connect_buttons] Iniciando conexão de botões")
        print(f"[DEBUG] Tem vars_dict: {hasattr(self, 'vars_dict')}")
        
        if not hasattr(self, 'vars_dict') or not self.vars_dict:
            print(f"[DEBUG] vars_dict não existe ou está vazio. Tentando novamente...")
            # Tentar novamente depois se ainda não estiver pronto
            self.after(100, self._connect_buttons)
            return
        
        print(f"[DEBUG] Chaves no vars_dict: {list(self.vars_dict.keys())}")
        
        # Buscar botões no vars_dict
        try:
            if "_then_button" in self.vars_dict:
                then_btn, _ = self.vars_dict["_then_button"]
                print(f"[DEBUG] Botão THEN encontrado: {then_btn}")
                if then_btn:
                    print(f"[DEBUG] Conectando comando ao botão THEN")
                    then_btn.config(command=self._edit_then)
                    self._update_button_text(then_btn, "then")
                    print(f"[DEBUG] Botão THEN conectado com sucesso")
            else:
                print(f"[DEBUG] Botão THEN NÃO encontrado no vars_dict!")
            
            if "_else_button" in self.vars_dict:
                else_btn, _ = self.vars_dict["_else_button"]
                print(f"[DEBUG] Botão ELSE encontrado: {else_btn}")
                if else_btn:
                    print(f"[DEBUG] Conectando comando ao botão ELSE")
                    else_btn.config(command=self._edit_else)
                    self._update_button_text(else_btn, "else_")
                    print(f"[DEBUG] Botão ELSE conectado com sucesso")
            else:
                print(f"[DEBUG] Botão ELSE NÃO encontrado no vars_dict!")
        except Exception as e:
            print(f"[DEBUG] ERRO ao conectar botões: {e}")
            import traceback
            traceback.print_exc()
            # Se houver erro, tentar novamente depois
            self.after(100, self._connect_buttons)
    
    def _update_button_text(self, button, block_name: str):
        """Atualiza o texto do botão com o contador de ações"""
        params = self.action_data.get("params", {})
        then_count = len(params.get("then", []))
        else_count = len(params.get("else_", []))
        total_count = then_count + else_count
        button.config(text=f"✏️ Editar Actions ({total_count} ação(ões) total)")
    
    def _edit_then(self):
        """Abre editor para bloco THEN"""
        print(f"[DEBUG] _edit_then CHAMADO!")
        print(f"[DEBUG] action_data: {self.action_data}")
        try:
            parent = self.winfo_toplevel()
            print(f"[DEBUG] Parent window: {parent}")
            print(f"[DEBUG] Criando IfActionsEditor...")
            editor = IfActionsEditor(parent, self.action_data, on_save=self._on_actions_saved)
            print(f"[DEBUG] IfActionsEditor criado: {editor}")
            editor.focus_set()
            editor.grab_set()
            print(f"[DEBUG] Editor configurado, aguardando...")
            editor.wait_window()  # Aguardar até a janela ser fechada
            print(f"[DEBUG] Editor fechado")
        except Exception as e:
            print(f"[DEBUG] ERRO ao abrir editor THEN: {e}")
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Erro", f"Erro ao abrir editor THEN: {e}")
    
    def _edit_else(self):
        """Abre editor para bloco ELSE"""
        print(f"[DEBUG] _edit_else CHAMADO!")
        print(f"[DEBUG] action_data: {self.action_data}")
        try:
            parent = self.winfo_toplevel()
            print(f"[DEBUG] Parent window: {parent}")
            print(f"[DEBUG] Criando IfActionsEditor...")
            editor = IfActionsEditor(parent, self.action_data, on_save=self._on_actions_saved)
            print(f"[DEBUG] IfActionsEditor criado: {editor}")
            editor.focus_set()
            editor.grab_set()
            print(f"[DEBUG] Editor configurado, aguardando...")
            editor.wait_window()  # Aguardar até a janela ser fechada
            print(f"[DEBUG] Editor fechado")
        except Exception as e:
            print(f"[DEBUG] ERRO ao abrir editor ELSE: {e}")
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Erro", f"Erro ao abrir editor ELSE: {e}")
    
    def _on_actions_saved(self):
        """Callback quando ações são salvas"""
        print(f"[DEBUG IfActionCard._on_actions_saved] Callback chamado")
        print(f"[DEBUG] action_data do card: {self.action_data}")
        print(f"[DEBUG] params no action_data: {self.action_data.get('params', {})}")
        
        # Verificar se os dados foram realmente salvos
        params = self.action_data.get("params", {})
        then_count = len(params.get("then", []))
        else_count = len(params.get("else_", []))
        total_count = then_count + else_count
        
        print(f"[DEBUG] Contadores: THEN={then_count}, ELSE={else_count}, TOTAL={total_count}")
        
        # Atualizar texto do botão
        if hasattr(self, 'vars_dict') and self.vars_dict:
            if "_edit_actions_button" in self.vars_dict:
                edit_btn, _ = self.vars_dict["_edit_actions_button"]
                if edit_btn:
                    edit_btn.config(text=f"✏️ Editar Actions ({total_count} ação(ões) total)")
                    print(f"[DEBUG] Botão atualizado com novo texto")
            else:
                print(f"[DEBUG] Botão _edit_actions_button não encontrado no vars_dict")
        else:
            print(f"[DEBUG] vars_dict não existe ou está vazio")
        
        # Notificar mudança
        if self.on_change:
            print(f"[DEBUG] Chamando on_change('actions_updated')")
            self.on_change("actions_updated")


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

        scroll_container = ttk.Frame(actions_frame)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        canvas = Canvas(scroll_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, command=canvas.yview)
        self.cards_container = ttk.Frame(canvas)
        self._actions_canvas = canvas
        self._actions_canvas_window = canvas.create_window((0, 0), window=self.cards_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        def _update_scroll_region(*_):
            bbox = canvas.bbox("all")
            if not bbox:
                return
            x1, y1, x2, y2 = bbox
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            content_h = y2 - y1
            # Região de scroll no mínimo do tamanho do viewport: evita rolar "para cima" com pouco conteúdo
            scroll_h = max(ch, content_h)
            scroll_w = max(cw, x2 - x1)
            canvas.configure(scrollregion=(0, 0, scroll_w, scroll_h))
            if content_h <= ch:
                canvas.yview_moveto(0)

        def _on_canvas_configure(e):
            canvas.itemconfig(self._actions_canvas_window, width=e.width)
            canvas.after_idle(_update_scroll_region)

        self.cards_container.bind("<Configure>", lambda e: canvas.after_idle(_update_scroll_region))
        canvas.bind("<Configure>", _on_canvas_configure)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_frame = ttk.Frame(actions_frame)
        scroll_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(scroll_frame, text="+ Adicionar action", command=self._add_action).pack(side="left", padx=2)
        self._new()

    def _add_action(self, action_data: dict | None = None):
        data = action_data or {"name": "goto", "params": {"url": "https://example.com"}}
        # Garantir estrutura correta para IF
        if data.get("name") == "if" and "params" not in data:
            data["params"] = {"condition": {"type": "equals"}, "then": [], "else_": []}
        
        # Usar IfActionCard se for ação IF
        if data.get("name") == "if":
            card = IfActionCard(
                self.cards_container,
                data,
                on_remove=lambda: self._remove_card(card),
                on_change=lambda direction: self._handle_if_card_change(card, direction),
            )
        else:
            card = ActionCard(
                self.cards_container,
                data,
                on_remove=lambda: self._remove_card(card),
                on_change=lambda direction: self._handle_card_change(card, direction),
            )
        card.pack(fill="x", pady=5)
        self.action_cards.append(card)
        self._update_card_order()
    
    def _handle_if_card_change(self, card: 'IfActionCard', direction: str):
        """Handler para mudanças no IfActionCard"""
        if direction == "type":
            # Se mudou o tipo, recriar o card
            idx = self.action_cards.index(card)
            data = card.get_data()
            card.destroy()
            self.action_cards.remove(card)
            
            if data.get("name") == "if":
                new_card = IfActionCard(
                    self.cards_container,
                    data,
                    on_remove=lambda: self._remove_card(new_card),
                    on_change=lambda d: self._handle_if_card_change(new_card, d),
                )
            else:
                new_card = ActionCard(
                    self.cards_container,
                    data,
                    on_remove=lambda: self._remove_card(new_card),
                    on_change=lambda d: self._handle_card_change(new_card, d),
                )
            new_card.pack(fill="x", pady=5)
            self.action_cards.insert(idx, new_card)
            self._reorder_cards_ui()
        elif direction in ("up", "down"):
            self._move_card(card, direction)
    
    def _handle_card_change(self, card: ActionCard, direction: str):
        """Handler para mudanças no ActionCard normal"""
        if direction == "type":
            # Se mudou para IF, recriar como IfActionCard
            idx = self.action_cards.index(card)
            data = card.get_data()
            card.destroy()
            self.action_cards.remove(card)
            
            if data.get("name") == "if":
                new_card = IfActionCard(
                    self.cards_container,
                    data,
                    on_remove=lambda: self._remove_card(new_card),
                    on_change=lambda d: self._handle_if_card_change(new_card, d),
                )
            else:
                new_card = ActionCard(
                    self.cards_container,
                    data,
                    on_remove=lambda: self._remove_card(new_card),
                    on_change=lambda d: self._handle_card_change(new_card, d),
                )
            new_card.pack(fill="x", pady=5)
            self.action_cards.insert(idx, new_card)
            self._reorder_cards_ui()
        elif direction in ("up", "down"):
            self._move_card(card, direction)

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
