import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import sys
import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading, webbrowser
import webbrowser
import threading

DATA_FILES = {
    "Intro": "data/intro.json",
    "Resource": "data/resource.json",
    "Custom": "data/custom.json",
    "Scene": "data/scenes.json",
    "Endings": "data/endings.json",
    "Setting": "data/setting.json",
}

class JSONEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.title("CYOA 데이터 편집기")
        self.geometry("1280x640")

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="저장 (Ctrl+S)", command=self.save_data_json)
        file_menu.add_command(label="로드 (Ctrl+L)", command=self.load_data_list)
        file_menu.add_command(label="빌드 및 실행 (Ctrl+R)", command=self.build_and_run)
        menubar.add_cascade(label="파일", menu=file_menu)
        self.config(menu=menubar)

        self.bind_all("<Control-s>", lambda event: self.save_data_json())
        self.bind_all("<Control-S>", lambda event: self.save_data_json())
        self.bind_all("<Control-l>", lambda event: self.load_data_list())
        self.bind_all("<Control-L>", lambda event: self.load_data_list())
        self.bind_all("<Control-r>", lambda event: self.build_and_run())
        self.bind_all("<Control-R>", lambda event: self.build_and_run())

        available_fonts = font.families()
        default_font = "Pretendard" if "Pretendard" in available_fonts else "맑은 고딕"

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        self.resource_data = {}
        self._suspend_update = False

        intro_frame = ttk.Frame(self.notebook)
        self.notebook.add(intro_frame, text="인트로")
        tk.Label(intro_frame, text="(인트로는 현재 수정 불가)\n즉석 쵸작이 끝나면 추가해볼수도?", font=(default_font, 14)).pack(pady=10)


        self.custom_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.custom_frame, text="커스텀")

        self.scene_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scene_frame, text="장면")

        self.endings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.endings_frame, text="엔딩")

        self.resource_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.resource_frame, text="변수")

        self.image_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.image_frame, text="이미지")

        self.setting_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.setting_frame, text="설정")

        self.build_custom_tab()
        self.build_scene_tab()
        self.build_endings_tab()
        self.build_resource_tab()
        self.build_image_tab()
        self.build_setting_tab()

        self.load_data_list()

        self.style = ttk.Style(self)
        self.style.configure("TFrame", background="#f4f4f4")
        self.style.configure("TLabel", background="#f4f4f4", font=(default_font, 10))
        self.style.configure("TCheckbutton", background="#f4f4f4", font=(default_font, 10))
        self.style.configure("TButton", font=(default_font, 10))
        self.configure(background="#f4f4f4")

    def load_data_list(self):
        self.load_resource_json()
        self.load_custom_json()
        self.load_scene_json()
        self.load_endings_json()
        self.load_image_list()
        self.load_setting_json()

    def load_image_list(self):
        image_dir = os.path.join(os.getcwd(), "image")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        self.image_files = [f for f in os.listdir(image_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
        self.image_listbox.delete(0, tk.END)
        for img in self.image_files:
            self.image_listbox.insert(tk.END, img)

    def make_scrollable_listbox(parent, height=6):
        frame = ttk.Frame(parent)
        scrollbar = ttk.Scrollbar(frame, orient='vertical')
        listbox = tk.Listbox(frame, height=height, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        return frame, listbox


    def build_resource_tab(self):
        self.resource_left = ttk.Frame(self.resource_frame, width=200)
        self.resource_left.pack(side='left', fill='y')
        self.resource_right = ttk.Frame(self.resource_frame, padding=10)
        self.resource_right.pack(side='right', expand=True, fill='both', padx=10, pady=10)

        title_label = ttk.Label(self.resource_right, text="변수 속성 설정", font=("맑은 고딕", 12, "bold"))
        title_label.pack(anchor='w', pady=(0, 10))

        listbox_frame = ttk.Frame(self.resource_left)
        listbox_frame.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical')
        self.resource_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.resource_listbox.yview)

        self.resource_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.resource_listbox.bind("<<ListboxSelect>>", self.on_resource_select)

        btns = ttk.Frame(self.resource_left)
        btns.pack(side='left', fill='y')

        add_btn = ttk.Button(btns, text="➕", command=self.add_resource)
        add_btn.pack(pady=2)
        self.create_tooltip(add_btn, "새 변수를 추가합니다.")

        self.del_btn = ttk.Button(btns, text="❌", command=self.delete_resource)
        self.del_btn.pack(pady=2)
        self.create_tooltip(self.del_btn, "선택한 변수를 삭제합니다. 단, 변수가 1개 이하일 경우 불가능합니다.")

        up_btn = ttk.Button(btns, text="⬆", command=self.move_resource_up)
        up_btn.pack(pady=2)
        self.create_tooltip(up_btn, "선택한 변수를 위로 이동합니다. 하단에 표시될 때, 위쪽의 변수가 먼저 표시됩니다.")

        down_btn = ttk.Button(btns, text="⬇", command=self.move_resource_down)
        down_btn.pack(pady=2)
        self.create_tooltip(down_btn, "선택한 변수를 아래로 이동합니다. 하단에 표시될 때, 위쪽의 변수가 먼저 표시됩니다.")

        self.resource_fields = {}

        for field, (label_text, tooltip_text) in {
            "name": ("변수 명", "이 값이 화면에 표시될 때 사용될 이름입니다."),
            "description": ("설명", "이 값의 역할을 설명합니다."),
            "realValue": ("초기값", "CYOA 시작 시 이 변수가 갖는 기본값입니다."),
        }.items():
            frame = ttk.Frame(self.resource_right, padding=5)
            frame.pack(fill='x', pady=6)
            label = ttk.Label(frame, text=label_text, width=12)
            label.pack(side='left')

            var = tk.StringVar()
            entry = tk.Entry(frame, textvariable=var, bg="#ffffff", font=("맑은 고딕", 10))
            var.trace_add("write", lambda *args: self.update_current_resource())

            entry.pack(side='left', fill='x', expand=True)
            self.create_tooltip(entry, tooltip_text)
            self.resource_fields[field] = var

        check_frame = ttk.Frame(self.resource_right, padding=(0, 5))
        check_frame.pack(anchor='w', fill='x', pady=(12, 6))

        ttk.Label(check_frame, text="표시 설정", font=("맑은 고딕", 10, "bold")).pack(anchor='w', pady=(0, 5))

        for field, label_text, tooltip_text in [
            ("show", "표시 여부", "이 변수를 하단의 UI에 표시할지 여부입니다."),
            ("showIfPositive", "양수일 때만 표시", "이 값이 0 이하나 false일 경우에는 표시하지 않습니다."),
            ("positive", "긍정적인 값", "이 변수가 높을수록 좋은 것인지 여부입니다. 증가하거나 감소할 때, 녹색으로 표기할지 빨간색으로 표기할지를 결정합니다."),
            ("summary", "요약에 표시", "이 변수가 엔딩 이후 최종 요약에서 표기될 지에 대한 여부입니다."),
        ]:
            var = tk.BooleanVar()
            check = ttk.Checkbutton(check_frame, text=label_text, variable=var, command=self.update_current_resource)
            check.pack(side='left', padx=12)
            self.create_tooltip(check, tooltip_text)
            self.resource_fields[field] = var


        # max/minValue with checkbox and combobox
        limit_info = {
            "maxValue": ("최대값 제한", "이 변수가 가질 수 있는 최대값입니다. 다른 변수를 지정하거나 직접 수치를 입력할 수 있습니다."),
            "minValue": ("최소값 제한", "이 변수가 가질 수 있는 최소값입니다. 다른 변수를 지정하거나 직접 수치를 입력할 수 있습니다."),
        }

        for field, (label_text, tooltip_text) in limit_info.items():
            frame = ttk.Frame(self.resource_right)
            frame.pack(fill='x', pady=(12, 2))
            label = ttk.Label(frame, text=label_text, width=12)
            label.pack(side='left')

            exists_var = tk.BooleanVar()
            check = ttk.Checkbutton(frame, variable=exists_var, command=self.update_maxmin_state)
            check.pack(side='left')

            input_var = tk.StringVar()
            input_entry = ttk.Entry(frame, textvariable=input_var)
            input_entry.pack(side='left', fill='x', expand=True)
            input_entry.bind("<FocusOut>", lambda e: self.update_current_resource())
            self.create_tooltip(input_entry, tooltip_text)

            combo = ttk.Combobox(frame, state='readonly')
            combo.pack(side='left')
            combo.bind("<<ComboboxSelected>>", lambda e, f=field, combo=combo, input_var=input_var, input_entry=input_entry, exists_var=exists_var: self.on_combobox_selected(f, combo, input_var, input_entry, exists_var))
            self.create_tooltip(combo, tooltip_text)

            self.resource_fields[field] = (exists_var, input_var, combo, input_entry)



    def build_custom_tab(self):
        self.custom_left = ttk.Frame(self.custom_frame, width=200)
        self.custom_left.pack(side='left', fill='y')
        self.custom_right = ttk.Frame(self.custom_frame, padding=10)
        self.custom_right.pack(side='right', expand=True, fill='both', padx=10, pady=10)

        # 카테고리 리스트
        listbox_frame = ttk.Frame(self.custom_left)
        listbox_frame.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical')
        self.custom_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.custom_listbox.yview)

        self.custom_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.custom_listbox.bind("<<ListboxSelect>>", self.on_custom_category_select)

        # 버튼 영역
        btns = ttk.Frame(self.custom_left)
        btns.pack(side='left', fill='y')
        add_btn = ttk.Button(btns, text="➕", command=self.add_custom_category)
        add_btn.pack(pady=2)
        self.create_tooltip(add_btn, "새 커스텀 카테고리를 추가합니다.")

        del_btn = ttk.Button(btns, text="❌", command=self.delete_custom_category)
        del_btn.pack(pady=2)
        self.create_tooltip(del_btn, "선택한 커스텀 카테고리를 삭제합니다.")

        move_up_btn = ttk.Button(btns, text="⬆", command=self.move_custom_up)
        move_up_btn.pack(pady=2)
        self.create_tooltip(move_up_btn, "선택한 카테고리를 위로 이동합니다.")

        move_down_btn = ttk.Button(btns, text="⬇", command=self.move_custom_down)
        move_down_btn.pack(pady=2)
        self.create_tooltip(move_down_btn, "선택한 카테고리를 아래로 이동합니다.")

        # 우측 편집 영역 (초기 라벨)
        self.custom_detail_label = ttk.Label(self.custom_right, text="카테고리를 선택하세요.", font=("맑은 고딕", 10))
        self.custom_detail_label.pack(anchor='w')

    def on_custom_category_select(self, event=None):
        selection = self.custom_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = self.custom_keys[idx]
        self.current_custom_key = key
        entry = self.custom_data[key]

        for widget in self.custom_right.winfo_children():
            widget.destroy()

        title_label = ttk.Label(self.custom_right, text=f"카테고리 속성 설정", font=("맑은 고딕", 11, "bold"))
        title_label.pack(anchor='w', pady=(0, 10))

        field_info = {
            "name": ("이름", "카테고리의 이름입니다.", "entry"),
            "description": ("설명", "카테고리에 대한 설명입니다.", "text"),
            "maxSelect": ("최대 선택 수", "선택할 수 있는 최대 선택지 수입니다. 0이라면 없음.", "int"),
            "required": ("필수 선택 수", "최소 선택해야 하는 선택지 수입니다. 0이라면 없음.", "int"),
        }

        self.custom_fields = {}
        self._suspend_update = True

        for field, (label_text, tooltip_text, field_type) in field_info.items():
            frame = ttk.Frame(self.custom_right, padding=5)
            frame.pack(fill='x', pady=4)
            label = ttk.Label(frame, text=label_text, width=12)
            label.pack(side='left')

            if field_type == "text":
                text_frame = ttk.Frame(frame)
                text_frame.pack(side='left', fill='both', expand=True)

                scrollbar = ttk.Scrollbar(text_frame, orient='vertical')
                text_widget = tk.Text(
                    text_frame, height=8, width=40, font=("맑은 고딕", 10),
                    wrap='word', yscrollcommand=scrollbar.set
                )
                scrollbar.config(command=text_widget.yview)

                text_widget.pack(side='left', fill='both', expand=True)
                scrollbar.pack(side='right', fill='y')

                self.create_tooltip(text_widget, tooltip_text)

                def make_on_modified(field):
                    def on_modified(event):
                        widget = event.widget
                        if widget.edit_modified():
                            widget.after_idle(self.update_current_custom)
                            widget.edit_modified(False)
                    return on_modified

                text_widget.bind("<<Modified>>", make_on_modified(field))

                self.custom_fields[field] = text_widget

            else:
                var = tk.StringVar()
                entry_widget = ttk.Entry(frame, textvariable=var)
                entry_widget.pack(side='left', fill='x', expand=True)
                self.create_tooltip(entry_widget, tooltip_text)
                var.trace_add("write", lambda *args: self.update_current_custom())
                self.custom_fields[field] = var


        for field in field_info:
            widget = self.custom_fields[field]
            value = entry.get(field, "")
            if isinstance(widget, tk.Text):
                widget.edit_modified(False)  # ✅ 이벤트 방지
                widget.delete("1.0", tk.END)
                widget.insert("1.0", str(value))
                widget.edit_modified(False)  # ✅ 다시 방지
            else:
                widget.set(str(value) if value is not None else "")

        self._suspend_update = False

        elements_label = ttk.Label(self.custom_right, text="선택지 목록", font=("맑은 고딕", 10, "bold"))
        elements_label.pack(anchor='w', pady=(12, 4))

        elements_frame = ttk.Frame(self.custom_right)
        elements_frame.pack(fill='both', expand=True)

        listbox_frame = ttk.Frame(elements_frame)
        listbox_frame.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical')
        self.element_listbox = tk.Listbox(listbox_frame, height=6, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.element_listbox.yview)

        self.element_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.element_listbox.bind("<Double-Button-1>", self.edit_selected_element)

        element_btns = ttk.Frame(elements_frame)
        element_btns.pack(side='left', padx=5)

        add_btn = ttk.Button(element_btns, text="➕", command=self.add_element)
        add_btn.pack(pady=2)
        self.create_tooltip(add_btn, "선택지를 추가합니다.")

        edit_btn = ttk.Button(element_btns, text="✏", command=self.edit_selected_element)
        edit_btn.pack(pady=2)
        self.create_tooltip(edit_btn, "선택지를 수정합니다.")

        del_btn = ttk.Button(element_btns, text="❌", command=self.delete_selected_element)
        del_btn.pack(pady=2)
        self.create_tooltip(del_btn, "선택지를 삭제합니다.")

        self.refresh_element_list()


    def update_current_custom(self):
        if getattr(self, "_suspend_update", False):
            return

        key = getattr(self, 'current_custom_key', None)
        if not key:
            return
        entry = self.custom_data.get(key, {})

        for field, widget in self.custom_fields.items():
            if isinstance(widget, tk.Text):
                text = widget.get("1.0", "end").strip()
                entry[field] = text
            else:
                val = widget.get().strip()
                if field in ("maxSelect", "required"):
                    try:
                        num = int(val)
                        if num > 0:
                            entry[field] = num
                        else:
                            entry.pop(field, None)
                    except:
                        entry.pop(field, None)
                else:
                    entry[field] = val

    def add_custom_category(self):
        def validate_id(new_id):
            if not new_id:
                return False, "ID를 입력하세요."
            if not new_id.isidentifier():
                return False, "ID는 영문자, 숫자, 밑줄(_)로 구성되어야 합니다."
            if new_id in self.custom_data:
                return False, "이미 존재하는 ID입니다."
            return True, ""

        popup = tk.Toplevel(self)
        popup.title("새 변수 ID")
        popup.resizable(False, False)

        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()
        width, height = 300, 150
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(popup, text="ID:").pack(pady=5)
        id_var = tk.StringVar()
        id_entry = ttk.Entry(popup, textvariable=id_var)
        id_entry.pack(pady=5)

        error_label = tk.Label(popup, text="", fg="red")
        error_label.pack()

        confirm_btn = ttk.Button(popup, text="확인", state='disabled')
        confirm_btn.pack(pady=5)

        def on_change(*args):
            valid, msg = validate_id(id_var.get())
            confirm_btn.config(state='normal' if valid else 'disabled')
            error_label.config(text=msg)

        id_var.trace_add('write', on_change)

        def on_confirm():
            new_id = id_var.get()
            self.custom_data[new_id] = {
                "name": "새 카테고리",
                "description": "",
                "elements": []
            }
            popup.destroy()
            self.refresh_custom_list(select_index=len(self.custom_data)-1)

        confirm_btn.config(command=on_confirm)
        id_entry.focus_set()
        popup.wait_window()

    def delete_custom_category(self):
        selection = self.custom_listbox.curselection()
        if not selection or len(self.custom_keys) <= 1:
            messagebox.showwarning("삭제 불가", "카테고리는 최소 1개 이상 존재해야 합니다.")
            return
        idx = selection[0]
        key = self.custom_keys[idx]
        name = self.custom_data[key].get("name", key)
        if messagebox.askyesno("삭제 확인", f"[{key}] 카테고리를 삭제하시겠습니까?"):
            self.custom_data.pop(key, None)
            self.refresh_custom_list(select_index=max(0, idx - 1))


    def refresh_element_list(self):
        key = getattr(self, 'current_custom_key', None)
        if not key:
            return
        self.element_listbox.delete(0, tk.END)
        elements = self.custom_data[key].get("elements", [])
        for i, el in enumerate(elements):
            title = el.get("title", f"선택지 {i+1}")
            self.element_listbox.insert(tk.END, title)

    def add_element(self):
        key = getattr(self, 'current_custom_key', None)
        if not key:
            return
        self.open_choice_editor('custom', key)

    def edit_selected_element(self, event=None):
        selection = self.element_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = getattr(self, 'current_custom_key', None)
        if not key:
            return
        elements = self.custom_data[key].get("elements", [])
        if 0 <= idx < len(elements):
            self.open_choice_editor('custom', key, elements[idx], idx)

    def delete_selected_element(self):
        selection = self.element_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = getattr(self, 'current_custom_key', None)
        if not key:
            return
        if messagebox.askyesno("삭제 확인", "이 선택지를 삭제하시겠습니까?"):
            elements = self.custom_data[key].get("elements", [])
            if 0 <= idx < len(elements):
                elements.pop(idx)
                self.refresh_element_list()

    def open_choice_editor(self, type, category_key, element=None, index=None, callback=None):
        popup = tk.Toplevel(self)
        popup.title("선택지 편집")
        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()
        width, height = 1024, 600
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill='both', expand=True)

        field_vars = {}
        data = element.copy() if element else {}

        if type == "custom" and not element:
            cat_tag = self.custom_data[category_key].get("name", category_key).replace(" ", "_")
            self_tag = "선택지"
            data["events"] = [
                {"type": "setValue", "target": "tags", "operation": "add", "value": cat_tag},
                {"type": "setValue", "target": "tags", "operation": "add", "value": self_tag, "hidden": True}
            ]
        elif type == "scene" and not element:
            data["events"] = []
            data["branch"] = [
                {
                    "priority": 0,
                    "weight": 1,
                    "type": "next"
                }
            ]


        def tip(widget, text):
            self.create_tooltip(widget, text)

        def labeled_entry(label_text, default="", parent=frame):
            sub = ttk.Frame(parent)
            sub.pack(fill='x', pady=4)
            label = ttk.Label(sub, text=label_text, width=12)
            label.pack(side='left')
            var = tk.StringVar(value=default)
            entry = ttk.Entry(sub, textvariable=var)
            entry.pack(side='left', fill='x', expand=True)
            return var

        def labeled_text(label_text, default="", parent=frame):
            sub = ttk.Frame(parent)
            sub.pack(fill='both', pady=4, expand=True)
            label = ttk.Label(sub, text=label_text)
            label.pack(anchor='w')
            text_frame = ttk.Frame(sub)
            text_frame.pack(fill='both', expand=True)
            scrollbar = ttk.Scrollbar(text_frame, orient='vertical')
            text_widget = tk.Text(text_frame, height=4, wrap='word', yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_widget.yview)
            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            text_widget.insert('1.0', default)
            return text_widget

        def labeled_spinbox(label_text, from_, to, default, parent=frame):
            sub = ttk.Frame(parent)
            sub.pack(fill='x', pady=4)
            label = ttk.Label(sub, text=label_text, width=12)
            label.pack(side='left')
            var = tk.IntVar(value=default)
            spin = ttk.Spinbox(sub, from_=from_, to=to, textvariable=var)
            spin.pack(side='left')
            return var

        def labeled_checkbox(label_text, default=False, parent=frame):
            sub = ttk.Frame(parent)
            sub.pack(fill='x', pady=4)
            var = tk.BooleanVar(value=default)
            check = ttk.Checkbutton(sub, text=label_text, variable=var)
            check.pack(side='left')
            return var

        upper_frame = ttk.Frame(popup)
        upper_frame.pack(fill='both', expand=True, padx=10, pady=(10, 4))
        lower_frame = ttk.Frame(popup)
        lower_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        left_frame = ttk.Frame(upper_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        right_frame = ttk.Frame(upper_frame, width=200)
        right_frame.pack(side='right', fill='both', padx=(10, 0))

        title_var = labeled_entry("제목", data.get("title", ""), parent=left_frame)
        field_vars["title"] = title_var
        tip(left_frame.winfo_children()[-1].winfo_children()[1], "선택지의 이름입니다.")

        text_widget = labeled_text("설명", data.get("text", ""), parent=left_frame)
        tip(text_widget, "선택지의 설명입니다.")

        default_width = data.get("width", 25 if type == "custom" else 50)
        width_var = labeled_spinbox("너비", 10, 100, default_width, parent=left_frame)
        field_vars["width"] = width_var
        tip(left_frame.winfo_children()[-1].winfo_children()[1], "선택지의 가로 길이입니다.")

        condition_var = tk.StringVar(value=data.get("condition", ""))
        condition_frame = ttk.Frame(left_frame)
        condition_frame.pack(fill='x', pady=4)
        ttk.Label(condition_frame, text="조건식", width=12).pack(side='left')
        condition_entry = ttk.Entry(condition_frame, textvariable=condition_var)
        condition_entry.pack(side='left', fill='x', expand=True)
        field_vars["condition"] = condition_var
        tip(condition_entry, "조건을 만족하지 않으면 비활성화됩니다.")

        condition_text_var = labeled_entry("조건 텍스트", data.get("conditionText", ""), parent=left_frame)
        field_vars["conditionText"] = condition_text_var
        tip(left_frame.winfo_children()[-1].winfo_children()[1], "조건을 설명하는 텍스트입니다. 비워두면 표시되지 않습니다.")

        hidden_var = tk.BooleanVar(value=data.get("hidden", False))
        hidden_check = ttk.Checkbutton(left_frame, text="숨김", variable=hidden_var)
        hidden_check.pack(anchor='w', pady=2)
        field_vars["hidden"] = hidden_var
        tip(hidden_check, "조건 미충족 시 선택지를 숨깁니다.")

        image_sub = ttk.Frame(right_frame)
        image_sub.pack(fill='x', pady=4)
        ttk.Label(image_sub, text="이미지", width=12).pack(side='left')
        image_var = tk.StringVar(value=data.get("image", ""))
        image_entry = ttk.Entry(image_sub, textvariable=image_var, state='readonly')
        image_entry.pack(side='left', fill='x', expand=True)
        tip(image_entry, "선택지 이미지 파일입니다.")

        def select_image():
            self.open_image_selector(lambda fname: (image_var.set(fname), update_image_preview()))

        image_btn = ttk.Button(image_sub, text="...", width=3, command=select_image)
        image_btn.pack(side='left', padx=4)
        tip(image_btn, "이미지 선택")

        image_preview = ttk.Label(right_frame, text="이미지 미리보기", anchor='center')
        image_preview.pack(fill='both', expand=True, pady=(4, 10))

        def update_image_preview():
            from PIL import Image, ImageTk
            fname = image_var.get()
            if not fname:
                image_preview.config(image='', text="이미지 미리보기")
                return
            path = os.path.join("image", fname)
            try:
                img = Image.open(path)
                image_preview.update_idletasks()
                max_w, max_h = image_preview.winfo_width() or 300, image_preview.winfo_height() or 300
                if img.width > max_w or img.height > max_h:
                    img.thumbnail((max_w, max_h))
                popup.tk_preview = ImageTk.PhotoImage(img)
                image_preview.config(image=popup.tk_preview, text='')
            except:
                image_preview.config(image='', text='불러오기 실패')

        update_image_preview()
        field_vars["image"] = image_var

        mid_frame = ttk.Frame(lower_frame)
        mid_frame.pack(fill='both', expand=True)
        events_label = ttk.Label(mid_frame, text="이벤트 목록", font=("맑은 고딕", 10, "bold"))
        events_label.pack(anchor='w', pady=(0, 4))

        event_frame = ttk.Frame(mid_frame)
        event_frame.pack(fill='both', expand=True)
        event_scroll = ttk.Scrollbar(event_frame, orient='vertical')
        event_listbox = tk.Listbox(event_frame, height=6, yscrollcommand=event_scroll.set)
        event_scroll.config(command=event_listbox.yview)
        event_listbox.pack(side='left', fill='both', expand=True)
        event_scroll.pack(side='right', fill='y')
        event_btns = ttk.Frame(event_frame)
        event_btns.pack(side='left', padx=5)

        def refresh_event_list():
            event_listbox.delete(0, tk.END)
            events = data.get("events", [])
            if type == "custom":
                visible_events = events[2:]
            else:
                visible_events = events
            for ev in visible_events:
                desc = f"{ev.get('type', '')} → {ev.get('target', '')} {ev.get('operation', '')} {ev.get('value', '')}"
                event_listbox.insert(tk.END, desc)

        def new_event():
            if "events" not in data:
                data["events"] = []
            self.open_event_editor(type, category_key, data["events"], index=None)
            refresh_event_list()

        def edit_event():
            selection = event_listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            if type == "custom":
                idx += 2
            self.open_event_editor(type, category_key, data["events"], index=idx)
            refresh_event_list()

        def delete_event():
            selection = event_listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            if type == "custom":
                idx += 2
            del data["events"][idx]
            refresh_event_list()

        event_listbox.bind("<Double-Button-1>", lambda e: edit_event())
        ttk.Button(event_btns, text="➕", command=new_event).pack(pady=2)
        ttk.Button(event_btns, text="✏", command=edit_event).pack(pady=2)
        ttk.Button(event_btns, text="❌", command=delete_event).pack(pady=2)

        refresh_event_list()

        branch_list = data.setdefault("branch", [{
            "priority": 0,
            "weight": 1,
            "type": "next"
        }]) if type == "scene" else []

        if type == "scene":
            ttk.Label(lower_frame, text="분기 목록", font=("맑은 고딕", 10, "bold")).pack(anchor='w', pady=(10, 4))

            branch_frame = ttk.Frame(lower_frame)
            branch_frame.pack(fill='both', expand=True)

            branch_scroll = ttk.Scrollbar(branch_frame, orient='vertical')
            branch_listbox = tk.Listbox(branch_frame, height=4, yscrollcommand=branch_scroll.set)
            branch_scroll.config(command=branch_listbox.yview)
            branch_listbox.pack(side='left', fill='both', expand=True)
            branch_scroll.pack(side='right', fill='y')

            branch_btns = ttk.Frame(branch_frame)
            branch_btns.pack(side='left', padx=5)

            def refresh_branch_list():
                branch_listbox.delete(0, tk.END)
                for b in branch_list:
                    desc = f"{b.get('type','next')} → {b.get('value','')}"
                    branch_listbox.insert(tk.END, desc)

            def add_branch():
                self.open_branch_editor(popup, category_key, branch_data=None, callback=lambda b: (branch_list.append(b), refresh_branch_list()))

            def edit_branch(event=None):
                sel = branch_listbox.curselection()
                if not sel:
                    return
                i = sel[0]
                self.open_branch_editor(popup, category_key, branch_data=branch_list[i], callback=lambda b: (branch_list.__setitem__(i, b), refresh_branch_list()))

            branch_listbox.bind("<Double-Button-1>", edit_branch)

            def delete_branch():
                idx = branch_listbox.curselection()
                if not idx:
                    return
                i = idx[0]
                if len(branch_list) <= 1:
                    messagebox.showwarning("삭제 불가", "최소 하나의 분기는 유지해야 합니다.")
                    return
                if messagebox.askyesno("삭제 확인", "이 분기를 삭제하시겠습니까?"):
                    branch_list.pop(i)
                    refresh_branch_list()

            ttk.Button(branch_btns, text="➕", command=add_branch).pack(pady=2)
            ttk.Button(branch_btns, text="✏", command=edit_branch).pack(pady=2)
            ttk.Button(branch_btns, text="❌", command=delete_branch).pack(pady=2)

            refresh_branch_list()



        def save():
            data["title"] = title_var.get().strip()
            data["text"] = text_widget.get("1.0", "end").strip()
            data["width"] = width_var.get()
            data["image"] = image_var.get().strip()
            data["conditionText"] = field_vars["conditionText"].get().strip()
            if not data["conditionText"]:
                data.pop("conditionText", None)

            cond = condition_var.get().strip()
            if cond:
                data["condition"] = cond
            elif "condition" in data:
                del data["condition"]

            if hidden_var.get():
                data["hidden"] = True
            elif "hidden" in data:
                del data["hidden"]

            data["type"] = "button"
            data["actionType"] = "toggle" if type == "custom" else "once"

            if type == "custom":
                cat_tag = self.custom_data[category_key].get("name", category_key).replace(" ", "_")
                self_tag = data["title"].replace(" ", "_")
                user_events = data.get("events", [])[2:] if len(data.get("events", [])) >= 2 else []
                data["events"] = [
                    {"type": "setValue", "target": "tags", "operation": "add", "value": cat_tag},
                    {"type": "setValue", "target": "tags", "operation": "add", "value": self_tag, "hidden": True},
                ] + user_events

            if type == "scene":
                data["branch"] = branch_list

            if type == "custom":
                elements = self.custom_data[category_key].setdefault("elements", [])
                if element and index is not None:
                    elements[index] = data
                else:
                    elements.append(data)

            if callback:
                callback(data)

            if type == "custom":
                self.refresh_element_list()

            popup.destroy()

        ttk.Button(popup, text="저장", command=save).pack(pady=(0, 10))
        self.wait_window(popup)


    def open_event_editor(self, type, category_key, events, index=None):
        popup = tk.Toplevel(self)
        popup.title("이벤트 편집")
        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()
        width, height = 500, 500
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill='both', expand=True)

        event_data = events[index] if index is not None else {}

        def tip(widget, text):
            self.create_tooltip(widget, text)

        type_label = ttk.Label(frame, text="이벤트 종류")
        type_label.pack(anchor='w')
        type_var = tk.StringVar(value="setValue")

        type_combo = ttk.Combobox(frame, textvariable=type_var, state='readonly')
        type_combo['values'] = ["setValue"]  # 강제 고정
        type_combo.config(state='disabled')
        type_combo.pack(fill='x', pady=4)
        tip(type_combo, "이벤트의 종류입니다. 현재는 setValue만 지원됩니다.")

        target_var = tk.StringVar()
        operation_var = tk.StringVar()
        value_var = tk.StringVar()

        condition_var = tk.StringVar(value=event_data.get("condition", ""))
        condition_label = ttk.Label(frame, text="조건식")
        condition_label.pack(anchor='w')
        condition_entry = ttk.Entry(frame, textvariable=condition_var)
        condition_entry.pack(fill='x', pady=2)
        tip(condition_entry, "이 이벤트가 적용될 조건입니다. 비워두면 항상 적용됩니다.")

        condition_text_var = tk.StringVar(value=event_data.get("conditionText", ""))
        condition_text_label = ttk.Label(frame, text="조건 텍스트")
        condition_text_label.pack(anchor='w')
        condition_text_entry = ttk.Entry(frame, textvariable=condition_text_var)
        condition_text_entry.pack(fill='x', pady=2)
        tip(condition_text_entry, "조건을 설명하는 텍스트입니다. 실제 기능과 무관하게 선택지에 표시됩니다.")

        hidden_var = tk.BooleanVar(value=event_data.get("hidden", False))
        hidden_check = ttk.Checkbutton(frame, text="선택지에 이 효과를 표기하지 않음", variable=hidden_var)
        hidden_check.pack(anchor='w', pady=(5, 10))
        tip(hidden_check, "선택지에 이 효과를 표시하지 않도록 설정합니다.")

        target_label = ttk.Label(frame, text="대상")
        target_label.pack(anchor='w')
        target_combo = ttk.Combobox(frame, textvariable=target_var, state='readonly')
        target_values = ["태그", "소지품"] + [self.resource_data[k].get("name", k) for k in self.resource_ids]
        target_combo['values'] = target_values
        target_combo.pack(fill='x', pady=2)
        tip(target_combo, "변수 또는 태그 중에 효과를 적용할 것을 고릅니다.")

        target_var.trace_add('write', lambda *args: update_operation_options())

        count_var = tk.StringVar(value=str(event_data.get("count", "")))

        count_frame = ttk.Frame(frame)
        count_label = ttk.Label(count_frame, text="수량 (count)")
        count_label.pack(anchor='w')
        count_entry = ttk.Entry(count_frame, textvariable=count_var)
        count_entry.pack(fill='x', pady=2)
        tip(count_entry, "추가/제거할 수량입니다. 비워두면 기본값 1, 0이면 전부 제거합니다.")
        count_frame.pack(fill='x', pady=2)
        count_frame.pack_forget()

        def update_operation_options(*args):
            selected = target_var.get()
            current_op = operation_var.get()

            if selected == "태그" or selected == "소지품":
                valid_ops = ["추가하기 (add)", "제거하기 (remove)"]
                default_op = "추가하기 (add)"
            else:
                valid_ops = ["값 설정 (=)", "더하기 (+)", "빼기 (-)", "곱하기 (*)", "나누기 (/)"]
                default_op = "값 설정 (=)"

            if selected == "소지품":
                count_frame.pack(fill='x', pady=2)
            else:
                count_frame.pack_forget()

            operation_combo['values'] = valid_ops
            if current_op in valid_ops:
                operation_var.set(current_op)
            else:
                operation_var.set(default_op)

        operation_label = ttk.Label(frame, text="연산 방식")
        operation_label.pack(anchor='w')
        operation_combo = ttk.Combobox(frame, textvariable=operation_var, state='readonly')
        operation_combo.pack(fill='x', pady=2)
        tip(operation_combo, "값을 어떻게 조작할지 설정합니다.")

        value_label = ttk.Label(frame, text="값")
        value_label.pack(anchor='w')
        value_entry = ttk.Entry(frame, textvariable=value_var)
        value_entry.pack(fill='x', pady=2)
        tip(value_entry, "적용할 값입니다.")

        def save():
            result = {
                "type": type_var.get(),
                "target": "tags" if target_var.get() == "태그" else "items" if target_var.get() == "소지품" else next(
                    (k for k in self.resource_ids if self.resource_data[k].get("name") == target_var.get()), target_var.get()),
                "value": value_var.get(),
            }
            op = operation_var.get()
            if op.startswith("추가"):
                result["operation"] = "add"
            elif op.startswith("제거"):
                result["operation"] = "remove"
            elif op.startswith("값 설정"):
                result["operation"] = "="
            elif op.startswith("더하기"):
                result["operation"] = "+"
            elif op.startswith("빼기"):
                result["operation"] = "-"
            elif op.startswith("곱하기"):
                result["operation"] = "*"
            elif op.startswith("나누기"):
                result["operation"] = "/"

            if condition_var.get().strip():
                result["condition"] = condition_var.get().strip()
            if condition_text_var.get().strip():
                result["conditionText"] = condition_text_var.get().strip()
            if hidden_var.get():
                result["hidden"] = True

            # count 값 추가
            if target_var.get() == "소지품":
                count_val = count_var.get().strip()
                if count_val.isdigit():
                    result["count"] = int(count_val)
                elif count_val == "0":
                    result["count"] = 0

            if index is not None:
                events[index] = result
            else:
                events.append(result)
            popup.destroy()



        save_btn = ttk.Button(popup, text="저장", command=save)
        save_btn.pack(pady=8)

        # 초기값 설정
        if event_data.get("target"):
            target = event_data["target"]
            if target == "tags":
                target_var.set("태그")
            elif target == "items":
                target_var.set("소지품")
            else:
                target_name = self.resource_data.get(target, {}).get("name", target)
                target_var.set(target_name)

        if event_data.get("operation"):
            op = event_data["operation"]
            display_op = {
                "=": "값 설정 (=)", "+": "더하기 (+)", "-": "빼기 (-)", "*": "곱하기 (*)", "/": "나누기 (/)",
                "add": "추가하기 (add)", "remove": "제거하기 (remove)"
            }.get(op, op)
            operation_var.set(display_op)

        if event_data.get("value"):
            value_var.set(str(event_data["value"]))

        update_operation_options()
        self.wait_window(popup)


    def open_branch_editor(self, parent, current_key, branch_data=None, callback=None):
        popup = tk.Toplevel(parent)
        popup.title("분기 편집")
        popup.transient(parent)
        popup.grab_set()

        popup.update_idletasks()
        width, height = 400, 320
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill='both', expand=True)

        # 기본값 설정
        data = branch_data.copy() if branch_data else {
            "type": "next",  # 기본값
            "priority": 0,
            "weight": 1
        }

        type_var = tk.StringVar(value=data.get("type", "next"))
        condition_var = tk.StringVar(value=data.get("condition", ""))
        value_var = tk.StringVar(value=data.get("value", ""))
        priority_var = tk.IntVar(value=data.get("priority", 0))
        weight_var = tk.IntVar(value=max(1, data.get("weight", 1)))

        # ▶ 타입 선택
        ttk.Label(frame, text="타입").pack(anchor='w')
        type_combo = ttk.Combobox(frame, textvariable=type_var, state='readonly')
        type_combo['values'] = ["next", "page", "ending"]
        type_combo.pack(fill='x', pady=4)

        # ▶ 조건식
        ttk.Label(frame, text="조건식").pack(anchor='w')
        condition_entry = ttk.Entry(frame, textvariable=condition_var)
        condition_entry.pack(fill='x', pady=4)

        # ▶ value (대상 선택)
        value_frame = ttk.Frame(frame)
        value_label = ttk.Label(value_frame, text="대상")
        value_label.pack(anchor='w')
        value_combo = ttk.Combobox(value_frame, textvariable=value_var, state='readonly')
        value_combo.pack(fill='x', pady=4)
        value_frame.pack(fill='x')

        def update_value_options(*args):
            t = type_var.get()
            if t == "page":
                pages = self.scene_data.get(self.current_scene_id, {}).get("pages", {})
                page_keys = list(pages.keys())
                value_combo['values'] = page_keys
                value_combo.configure(state='readonly')
            elif t == "ending":
                ending_keys = list(self.endings_data.keys()) if isinstance(self.endings_data, dict) else []
                value_combo['values'] = ending_keys
                value_combo.configure(state='readonly')
            else:
                value_combo.set("")
                value_combo.configure(state='disabled')

        type_var.trace_add('write', update_value_options)
        update_value_options()

        # ▶ 우선순위와 가중치 (한 줄)
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=6)
        ttk.Label(row, text="우선순위", width=8).pack(side='left')
        priority_entry = ttk.Entry(row, textvariable=priority_var, width=10)
        priority_entry.pack(side='left', padx=(0, 10))
        ttk.Label(row, text="가중치", width=6).pack(side='left')
        weight_entry = ttk.Entry(row, textvariable=weight_var, width=10)
        weight_entry.pack(side='left')

        # ▶ 저장 버튼
        def save():
            t = type_var.get()
            result = {
                "type": t,
                "condition": condition_var.get().strip(),
                "priority": int(priority_var.get()),
                "weight": max(1, int(weight_var.get()))
            }
            if t in ["page", "ending"]:
                result["value"] = value_var.get().strip()

            if not result["condition"]:
                del result["condition"]

            if callback:
                callback(result)
            popup.destroy()

        ttk.Button(frame, text="저장", command=save).pack(pady=10)

        self.wait_window(popup)


    def build_scene_tab(self):
        self.scene_data = {}  # id를 key로 하는 딕셔너리
        self.current_scene_id = None
        self.scene_fields = {}
        self.page_widgets = {}

        # 좌우 레이아웃
        self.scene_left = ttk.Frame(self.scene_frame, width=200)
        self.scene_left.pack(side='left', fill='y')
        self.scene_right = ttk.Frame(self.scene_frame, padding=10)
        self.scene_right.pack(side='right', expand=True, fill='both', padx=10, pady=10)

        # 리스트박스 및 스크롤
        self.scene_listbox = tk.Listbox(self.scene_left)
        self.scene_listbox.pack(side='left', fill='both', expand=True)
        self.scene_listbox.bind("<<ListboxSelect>>", self.on_scene_select)

        scrollbar = ttk.Scrollbar(self.scene_left, orient="vertical", command=self.scene_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.scene_listbox.config(yscrollcommand=scrollbar.set)

        # 버튼 프레임
        btn_frame = ttk.Frame(self.scene_left)
        btn_frame.pack(fill='x', pady=4)

        ttk.Button(btn_frame, text="➕", command=self.add_scene).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text="❌", command=self.delete_scene).pack(fill='x', pady=2)

        self.build_scene_detail_form()


    def build_scene_detail_form(self):
        self.scene_fields.clear()

        title = ttk.Label(self.scene_right, text="장면 속성 설정", font=("맑은 고딕", 12, "bold"))
        title.pack(anchor='w', pady=(0, 10))

        field_info = {
            "title": ("제목", "장면의 이름입니다."),
            "condition": ("조건식", "조건을 만족할 경우에만 발생합니다."),
            "priority": ("우선순위", "높을수록 먼저 평가됩니다."),
            "weight": ("가중치", "확률에 영향을 줍니다.")
        }

        for field, (label, tip) in field_info.items():
            frame = ttk.Frame(self.scene_right)
            frame.pack(fill='x', pady=2)
            ttk.Label(frame, text=label, width=12).pack(side='left')
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var)
            entry.pack(side='left', fill='x', expand=True)
            entry.bind("<FocusOut>", lambda e: self.update_current_scene())
            self.create_tooltip(entry, tip)
            self.scene_fields[field] = var

        var = tk.BooleanVar()
        check = ttk.Checkbutton(self.scene_right, text="반복 가능 여부", variable=var, command=self.update_current_scene)
        check.pack(anchor='w', padx=10, pady=4)
        self.create_tooltip(check, "이 장면이 여러 번 발생할 수 있는지 여부입니다.")
        self.scene_fields["repeatable"] = var

        ttk.Label(self.scene_right, text="페이지 목록", font=("맑은 고딕", 10, "bold")).pack(anchor='w', pady=(20, 4))

        page_frame = ttk.Frame(self.scene_right)
        page_frame.pack(fill='both', expand=True)

        self.page_listbox = tk.Listbox(page_frame, height=6)
        self.page_listbox.pack(side='left', fill='both', expand=True)
        self.page_listbox.bind("<Double-Button-1>", self.edit_page)

        page_btns = ttk.Frame(page_frame)
        page_btns.pack(side='left', padx=5)
        ttk.Button(page_btns, text="➕", command=self.add_page).pack(pady=2)
        ttk.Button(page_btns, text="✏", command=self.edit_page).pack(pady=2)
        ttk.Button(page_btns, text="❌", command=self.delete_page).pack(pady=2)


    def refresh_scene_list(self, selected_id=0):
        self.scene_listbox.delete(0, tk.END)
        self.scene_keys = sorted(self.scene_data.keys(), key=lambda k: -self.scene_data[k].get("priority", 0))
        for k in self.scene_keys:
            p = self.scene_data[k].get("priority", 0)
            self.scene_listbox.insert(tk.END, f"{p}: {k}")
        if self.scene_keys:
            if selected_id and selected_id in self.scene_keys:
                select_index = self.scene_keys.index(selected_id)
            else:
                select_index = 0

            self.scene_listbox.select_set(select_index)
            self.scene_listbox.event_generate("<<ListboxSelect>>")


    def on_scene_select(self, event=None):
        selection = self.scene_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = self.scene_keys[idx]
        self.current_scene_id = key
        entry = self.scene_data[key]

        for k, var in self.scene_fields.items():
            val = entry.get(k, False if isinstance(var, tk.BooleanVar) else "")
            var.set(val)

        self.refresh_page_list()


    def update_current_scene(self):
        if not getattr(self, "current_scene_id", None):
            return

        currentKey = self.current_scene_id

        current_data = self.scene_data[currentKey]
        new_priority = int(self.scene_fields["priority"].get())

        should_refresh = new_priority != current_data.get("priority", 0)

        updated = {}
        for k, var in self.scene_fields.items():
            if isinstance(var, tk.BooleanVar):
                updated[k] = var.get()
            else:
                val = var.get()
                try:
                    val = int(val) if k in ["priority", "weight"] else val
                except:
                    pass
                updated[k] = val

        if "condition" in updated and not updated["condition"].strip():
            self.scene_data[self.current_scene_id].pop("condition", None)
        else:
            self.scene_data[self.current_scene_id]["condition"] = updated.get("condition", "")

        for key, value in updated.items():
            if key != "condition":
                self.scene_data[self.current_scene_id][key] = value

        if should_refresh:
            self.refresh_scene_list(selected_id=currentKey)


    def add_scene(self):
        from tkinter.simpledialog import askstring
        new_id = askstring("ID 입력", "새 장면 ID를 입력하세요:")
        if not new_id:
            return
        if new_id in self.scene_data:
            messagebox.showerror("중복 오류", "이미 존재하는 ID입니다.")
            return

        self.scene_data[new_id] = {
            "title": "새 장면",
            "priority": 0,
            "weight": 1,
            "repeatable": False,
            "pages": {
                "start": {
                    "summary": "",
                    "elements": [
                        {"type": "textbox", "title": "", "text": ""},
                        {
                            "type": "choice",
                            "elements":[
                                {
                                    "type":"button", "title":"계속", "width":80, "events":[],
                                    "branch": [ 
                                        {
                                            "priority": 0,
                                            "weight": 1,
                                            "type": "next"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        self.refresh_scene_list(selected_id=new_id)


    def delete_scene(self):
        selection = self.scene_listbox.curselection()
        if not selection:
            return

        # 장면이 하나 뿐이면 삭제 방지
        if len(self.scene_keys) <= 1:
            messagebox.showwarning("삭제 불가", "장면은 최소 하나 이상 존재해야 합니다.")
            return

        idx = selection[0]
        key = self.scene_keys[idx]

        if messagebox.askyesno("삭제 확인", f"장면 '{key}'을 삭제하시겠습니까?"):
            del self.scene_data[key]
            remaining_keys = sorted(self.scene_data.keys(), key=lambda k: -self.scene_data[k].get("priority", 0))
            next_key = remaining_keys[max(0, idx - 1)] if remaining_keys else None
            self.refresh_scene_list(selected_id=next_key)


    def refresh_page_list(self):
        self.page_listbox.delete(0, tk.END)
        if not self.current_scene_id or self.current_scene_id not in self.scene_data:
            return

        pages = self.scene_data[self.current_scene_id].get("pages", {})
        for key in pages:
            page = pages[key]
            textbox = next((e for e in page.get("elements", []) if e.get("type") == "textbox"), {})
            title = textbox.get("title", "").strip() or "제목 없음"
            summary = page.get("summary", "").replace("\n", " ").strip()
            summary_preview = (summary[:30] + "...") if len(summary) > 30 else summary
            line = f"{key} | {title} | {summary_preview}"
            self.page_listbox.insert(tk.END, line)


    def add_page(self):
        self.open_page_editor()

    def edit_page(self, event=None):
        selection = self.page_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        self.open_page_editor(index=idx)

    def delete_page(self):
        selection = self.page_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = list(self.scene_data[self.current_scene_id]["pages"].keys())[idx]

        if key == "start":
            messagebox.showwarning("삭제 불가", "시작 페이지는 삭제할 수 없습니다.")
            return

        if messagebox.askyesno("삭제 확인", f"페이지 '{key}'를 삭제하시겠습니까?"):
            self.scene_data[self.current_scene_id]["pages"].pop(key)
            self.refresh_page_list()


    def open_page_editor(self, index=None):
        popup = tk.Toplevel(self)
        popup.title("페이지 편집")
        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()
        width, height = 960, 560
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        key = None
        data = {}
        pages = self.scene_data[self.current_scene_id].setdefault("pages", {})
        
        if index is not None:
            key = list(pages.keys())[index]
            data = pages[key].copy()
        else:
            base = "page"
            existing_keys = set(pages.keys())
            i = 1
            while f"{base}_{i}" in existing_keys:
                i += 1
            key = f"{base}_{i}"

        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill='both', expand=True)

        top_frame = ttk.Frame(frame)
        top_frame.pack(fill='both', expand=True)

        left_area = ttk.Frame(top_frame)
        left_area.pack(side='left', fill='both', expand=True, padx=(0, 10))

        right_area = ttk.Frame(top_frame, width=200)
        right_area.pack(side='right', fill='y')


        textbox = next((e for e in data.get("elements", []) if e.get("type") == "textbox"), {})
        text_title = tk.StringVar(value=textbox.get("title", ""))
        ttk.Label(left_area, text="제목").pack(anchor='w', pady=(8, 0))
        ttk.Entry(left_area, textvariable=text_title).pack(fill='x', pady=2)

        text_content = tk.Text(left_area, height=6, wrap='word')
        text_content.insert("1.0", textbox.get("text", ""))

        ttk.Label(left_area, text="내용").pack(anchor='w')
        text_content.pack(fill='both', pady=2)

        summary_widget = tk.Text(left_area, height=4, wrap='word')
        summary_widget.insert("1.0", data.get("summary", ""))
        ttk.Label(left_area, text="요약").pack(anchor='w')
        summary_widget.pack(fill='both', pady=2)

        image_frame = ttk.Frame(right_area)
        image_frame.pack(fill='x', pady=4)

        ttk.Label(image_frame, text="이미지").pack(anchor='w')

        image_var = tk.StringVar(value=textbox.get("image", ""))
        image_preview = ttk.Label(image_frame, text="이미지 미리보기")
        image_preview.pack(fill='both', expand=True, pady=2)

        def update_preview():
            from PIL import Image, ImageTk
            fname = image_var.get()
            if not fname:
                image_preview.config(image='', text="이미지 미리보기")
                return
            path = os.path.join("image", fname)
            try:
                img = Image.open(path)
                img.thumbnail((200, 200))
                preview = ImageTk.PhotoImage(img)
                image_preview.config(image=preview, text='')
                image_preview.image = preview
            except:
                image_preview.config(image='', text='불러오기 실패')

        update_preview()

        def select_image():
            self.open_image_selector(lambda fname: (image_var.set(fname), update_preview()))

        btn_frame = ttk.Frame(image_frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text="선택", command=select_image).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="제거", command=lambda: (image_var.set(""), update_preview())).pack(side='left', padx=2)

        # 선택지 목록 Label
        choice_frame = ttk.Frame(popup)
        choice_frame.pack(fill='both', expand=False, pady=(10, 0))

        ttk.Label(choice_frame, text="선택지 목록", font=("맑은 고딕", 10, "bold")).pack(anchor='w', pady=(8, 4))

        choice_elements = []
        for e in data.get("elements", []):
            if e.get("type") == "choice":
                choice_elements = e.get("elements", [])
                break

        if not choice_elements:
            choice_elements.append({
                "type": "button",
                "title": "계속",
                "actionType": "once",
                "width": 80,
                "events": [],
                "branch": [
                    {
                        "priority": 0,
                        "weight": 1,
                        "type": "next"
                    }
                ]
            })

        self.choice_listbox = tk.Listbox(choice_frame, height=6)
        self.choice_listbox.pack(side='left', fill='both', expand=True)

        def refresh_choice_list():
            self.choice_listbox.delete(0, tk.END)
            for btn in choice_elements:
                self.choice_listbox.insert(tk.END, btn.get("title", "(제목 없음)"))

        def add_choice():
            def on_save(choice_data):
                choice_elements.append(choice_data)
                refresh_choice_list()
            self.open_choice_editor("scene", key, element=None, index=None, callback=on_save)

        def edit_choice(event=None):
            selection = self.choice_listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            def on_save(choice_data):
                choice_elements[idx] = choice_data
                refresh_choice_list()
            self.open_choice_editor("scene", key, element=choice_elements[idx], index=idx, callback=on_save)

        self.choice_listbox.bind("<Double-Button-1>", edit_choice)

        def delete_choice():
            selection = self.choice_listbox.curselection()
            if not selection:
                return
            idx = selection[0]
            if messagebox.askyesno("삭제 확인", "이 선택지를 삭제하시겠습니까?"):
                del choice_elements[idx]
                refresh_choice_list()

        btn_frame = ttk.Frame(choice_frame)
        btn_frame.pack(side='left', padx=4)
        ttk.Button(btn_frame, text="➕", command=add_choice).pack(pady=2)
        ttk.Button(btn_frame, text="✏", command=edit_choice).pack(pady=2)
        ttk.Button(btn_frame, text="❌", command=delete_choice).pack(pady=2)

        refresh_choice_list()

        # 저장 시 data['elements']에 textbox + choice를 넣어야 함
        def save():
            elements = []
            # textbox
            textbox_data = {
                "type": "textbox",
                **({"title": text_title.get().strip()} if text_title.get().strip() else {}),
                "text": text_content.get("1.0", "end").strip()
            }
            elements.append(textbox_data)

            # choice
            if choice_elements:
                elements.append({
                    "type": "choice",
                    "elements": choice_elements
                })

            pages[key] = {
                "summary": summary_widget.get("1.0", "end").strip(),
                "elements": elements
            }
            popup.destroy()
            self.refresh_page_list()

        ttk.Button(popup, text="저장", command=save).pack(pady=10)
        self.wait_window(popup)


    def build_endings_tab(self):
        self.ending_left = ttk.Frame(self.endings_frame, width=200)
        self.ending_left.pack(side='left', fill='y')
        self.ending_right = ttk.Frame(self.endings_frame, padding=10)
        self.ending_right.pack(side='right', expand=True, fill='both', padx=10, pady=10)

        self.ending_listbox = tk.Listbox(self.ending_left)
        self.ending_listbox.pack(side='left', fill='both', expand=True)
        self.ending_listbox.bind("<<ListboxSelect>>", self.on_ending_select)

        scrollbar = ttk.Scrollbar(self.ending_left, orient="vertical", command=self.ending_listbox.yview)
        self.ending_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.ending_btn_frame = ttk.Frame(self.ending_left)
        self.ending_btn_frame.pack(fill='x', pady=4)

        ttk.Button(self.ending_btn_frame, text="➕", command=self.add_ending).pack(fill='x', pady=2)
        self.del_ending_btn = ttk.Button(self.ending_btn_frame, text="❌", command=self.delete_ending)
        self.del_ending_btn.pack(fill='x', pady=2)

        # 오른쪽은 선택 시 생성
        self.ending_fields = {}
        self.ending_image_preview = None

    def on_ending_select(self, event=None):
        selection = self.ending_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = self.ending_keys[idx]
        self.current_ending_id = key

        data = self.endings_data[key]
        textbox = data.get("elements", [{}])[0]

        for widget in self.ending_right.winfo_children():
            widget.destroy()

        def labeled_entry(label_text, var):
            frame = ttk.Frame(self.ending_right)
            frame.pack(fill='x', pady=4)
            ttk.Label(frame, text=label_text, width=10).pack(side='left')
            entry = ttk.Entry(frame, textvariable=var)
            entry.pack(side='left', fill='x', expand=True)
            entry.bind("<FocusOut>", lambda e: self.update_current_ending())

        self.ending_fields["title"] = tk.StringVar(value=data.get("title", ""))
        self.ending_fields["condition"] = tk.StringVar(value=data.get("condition", ""))
        self.ending_fields["priority"] = tk.IntVar(value=data.get("priority", 0))
        self.ending_fields["image"] = tk.StringVar(value=textbox.get("image", ""))

        labeled_entry("제목", self.ending_fields["title"])
        labeled_entry("조건식", self.ending_fields["condition"])
        labeled_entry("우선도", self.ending_fields["priority"])

        ttk.Label(self.ending_right, text="내용").pack(anchor='w', pady=(8, 2))
        text_widget = tk.Text(self.ending_right, height=6, wrap='word')
        text_widget.insert("1.0", textbox.get("text", ""))
        text_widget.pack(fill='both', expand=True)
        text_widget.edit_modified(False)

        def on_ending_text_modified(event):
            widget = event.widget
            if widget.edit_modified():
                widget.edit_modified(False)
                self.update_current_ending()
        text_widget.bind("<<Modified>>", on_ending_text_modified)
        self.ending_fields["text"] = text_widget

        img_frame = ttk.Frame(self.ending_right)
        img_frame.pack(fill='x', pady=4)
        ttk.Label(img_frame, text="이미지", width=10).pack(side='left')
        image_entry = ttk.Entry(img_frame, textvariable=self.ending_fields["image"], state='readonly')
        image_entry.pack(side='left', fill='x', expand=True)

        def on_image_selected(f):
            self.ending_fields["image"].set(f)
            self.update_ending_image_preview()
            self.update_current_ending()

        ttk.Button(img_frame, text="...", command=lambda: self.open_image_selector(on_image_selected)).pack(side='left')

        self.ending_image_preview = ttk.Label(self.ending_right, text="이미지 미리보기", anchor='center')
        self.ending_image_preview.pack(fill='both', pady=4, expand=True)
        self.update_ending_image_preview()


    def update_ending_image_preview(self):
        from PIL import Image, ImageTk
        fname = self.ending_fields["image"].get()
        if not fname:
            self.ending_image_preview.config(image='', text="이미지 미리보기")
            return
        path = os.path.join("image", fname)
        try:
            img = Image.open(path)
            img.thumbnail((300, 300))
            self.tk_ending_preview = ImageTk.PhotoImage(img)
            self.ending_image_preview.config(image=self.tk_ending_preview, text='')
        except:
            self.ending_image_preview.config(image='', text='불러오기 실패')


    def update_current_ending(self):
        if not getattr(self, "current_ending_id", None):
            return

        key = self.current_ending_id

        current_data = self.endings_data[key]
        new_priority = int(self.ending_fields["priority"].get())

        should_refresh = new_priority != current_data.get("priority", 0)

        updated = {
            "title": self.ending_fields["title"].get().strip(),
            "priority": int(self.ending_fields["priority"].get()),
            "elements": [
                {
                    "type": "textbox",
                    "text": self.ending_fields["text"].get("1.0", "end").strip(),
                }
            ]
        }
        if self.ending_fields["condition"].get().strip():
            updated["condition"] = self.ending_fields["condition"].get().strip()
        image_val = self.ending_fields["image"].get().strip()
        if image_val:
            updated["elements"][0]["image"] = image_val

        self.endings_data[key] = updated

        if should_refresh:
            self.refresh_ending_list(selected_id=key)



    def add_ending(self):
        from tkinter.simpledialog import askstring
        new_id = askstring("ID 입력", "새 엔딩 ID를 입력하세요:")
        if not new_id:
            return
        if new_id in self.endings_data:
            messagebox.showerror("중복 오류", "이미 존재하는 ID입니다.")
            return

        self.endings_data[new_id] = {
            "title": "새 엔딩",
            "priority": 0,
            "elements": [
                {
                    "type": "textbox",
                    "text": ""
                }
            ]
        }
        self.refresh_ending_list(selected_id=new_id)


    def delete_ending(self):
        if len(self.endings_data) <= 1:
            messagebox.showwarning("삭제 불가", "엔딩은 최소 하나 이상 존재해야 합니다.")
            return
        selection = self.ending_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = self.ending_keys[idx]
        if messagebox.askyesno("삭제 확인", "이 엔딩을 삭제하시겠습니까?"):
            del self.endings_data[key]
            remaining_keys = sorted(self.endings_data.keys(), key=lambda k: -self.endings_data[k].get("priority", 0))
            next_key = remaining_keys[max(0, idx - 1)] if remaining_keys else None
            self.refresh_ending_list(selected_id=next_key)


    def refresh_ending_list(self, selected_id=None):
        self.ending_listbox.delete(0, tk.END)

        self.ending_keys = sorted(self.endings_data.keys(), key=lambda k: -self.endings_data[k].get("priority", 0))

        for k in self.ending_keys:
            p = self.endings_data[k].get("priority", 0)
            self.ending_listbox.insert(tk.END, f"{p}: {k}")

        if self.ending_keys:
            if selected_id and selected_id in self.ending_keys:
                select_index = self.ending_keys.index(selected_id)
            else:
                select_index = 0

            self.ending_listbox.select_set(select_index)
            self.ending_listbox.see(select_index)
            self.on_ending_select()


    def build_image_tab(self):
        self.image_left = ttk.Frame(self.image_frame, width=250)
        self.image_left.pack(side='left', fill='y')
        self.image_right = ttk.Frame(self.image_frame, padding=10)
        self.image_right.pack(side='right', expand=True, fill='both', padx=10, pady=10)

        # 리스트 및 스크롤바
        listbox_frame = ttk.Frame(self.image_left)
        listbox_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical')
        self.image_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.image_listbox.yview)
        self.image_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.image_listbox.bind("<<ListboxSelect>>", self.on_image_select)

        btn_frame = ttk.Frame(self.image_left)
        btn_frame.pack(fill='x', pady=4)

        add_btn = ttk.Button(btn_frame, text="➕", command=self.add_image)
        add_btn.pack(fill='x', padx=4, pady=2)
        self.create_tooltip(add_btn, "이미지 파일을 추가합니다.")

        del_btn = ttk.Button(btn_frame, text="❌", command=self.delete_image)
        del_btn.pack(fill='x', padx=4, pady=2)
        self.create_tooltip(del_btn, "선택한 이미지를 삭제합니다.")

        # 우측 미리보기 영역
        self.image_label = ttk.Label(self.image_right, text="이미지를 선택하세요.", anchor='center')
        self.image_label.pack(fill='both', expand=True)

    def on_image_select(self, event=None):
        selection = self.image_listbox.curselection()
        if not selection:
            self.image_label.config(text="이미지를 선택하세요.", image='')
            return
        filename = self.image_files[selection[0]]
        image_path = os.path.join("image", filename)
        try:
            from PIL import Image, ImageTk
            image = Image.open(image_path)
            
            self.image_label.update_idletasks()
            max_width = self.image_label.winfo_width() or 512
            max_height = self.image_label.winfo_height() or 512

            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height))

            self.tk_preview_image = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.tk_preview_image, text='')
        except Exception as e:
            self.image_label.config(text=f"이미지 표시 실패: {e}", image='')

    def add_image(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if not file_path:
            return
        image_dir = os.path.join(os.getcwd(), "image")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        filename = os.path.basename(file_path)
        dest_path = os.path.join(image_dir, filename)
        try:
            import shutil
            shutil.copy(file_path, dest_path)
            self.load_image_list()
        except Exception as e:
            messagebox.showerror("복사 실패", str(e))

    def delete_image(self):
        selection = self.image_listbox.curselection()
        if not selection:
            return
        filename = self.image_files[selection[0]]
        if messagebox.askyesno("삭제 확인", f"이미지 '{filename}' 을 삭제하시겠습니까?"):
            try:
                os.remove(os.path.join("image", filename))
                self.load_image_list()
                self.image_label.config(text="이미지를 선택하세요.", image='')
            except Exception as e:
                messagebox.showerror("삭제 실패", str(e))

    def open_image_selector(self, callback):
        popup = tk.Toplevel(self)
        popup.title("이미지 선택")
        popup.transient(self)
        popup.grab_set()
        popup.update_idletasks()
        width, height = 720, 640
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        main_frame = ttk.Frame(popup, padding=10)
        main_frame.pack(fill='both', expand=True)

        left_frame = ttk.Frame(main_frame, width=200)
        left_frame.pack(side='left', fill='y')

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))

        bottom_frame = ttk.Frame(popup)
        bottom_frame.pack(fill='x', pady=8)

        # 리스트박스 + 스크롤바
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical')
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def refresh_image_list():
            image_dir = os.path.join(os.getcwd(), "image")
            files = [f for f in os.listdir(image_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
            listbox.delete(0, tk.END)
            for f in files:
                listbox.insert(tk.END, f)
            return files

        # 미리보기
        preview_label = ttk.Label(right_frame, text="미리보기", anchor='center')
        preview_label.pack(fill='both', expand=True)

        def on_select(event=None):
            sel = listbox.curselection()
            if not sel:
                preview_label.config(image='', text='미리보기')
                return
            fname = listbox.get(sel[0])
            path = os.path.join("image", fname)
            try:
                from PIL import Image, ImageTk
                img = Image.open(path)
                preview_label.update_idletasks()
                max_w, max_h = preview_label.winfo_width() or 400, preview_label.winfo_height() or 400
                if img.width > max_w or img.height > max_h:
                    img.thumbnail((max_w, max_h))
                img.thumbnail((512, 512))
                popup.tk_preview = ImageTk.PhotoImage(img)
                preview_label.config(image=popup.tk_preview, text='')
            except:
                preview_label.config(image='', text='불러오기 실패')

        listbox.bind("<<ListboxSelect>>", on_select)

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            fname = listbox.get(sel[0])
            callback(fname)
            popup.destroy()

        def add_new():
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
            if not file_path:
                return
            import shutil
            image_dir = os.path.join(os.getcwd(), "image")
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            fname = os.path.basename(file_path)
            dest_path = os.path.join(image_dir, fname)
            try:
                shutil.copy(file_path, dest_path)
                refresh_image_list()
            except Exception as e:
                messagebox.showerror("복사 실패", str(e))

        select_btn = ttk.Button(bottom_frame, text="선택", command=confirm)
        select_btn.pack(side='left', padx=4)

        add_btn = ttk.Button(bottom_frame, text="추가", command=add_new)
        add_btn.pack(side='left', padx=4)
        self.create_tooltip(add_btn, "새 이미지를 추가합니다.")

        cancel_btn = ttk.Button(bottom_frame, text="취소", command=popup.destroy)
        cancel_btn.pack(side='left', padx=4)

        remove_btn = ttk.Button(bottom_frame, text="제거", command=lambda: (callback(""), popup.destroy()))
        remove_btn.pack(side='left', padx=4)
        self.create_tooltip(remove_btn, "이미지를 선택하지 않도록 설정합니다.")

        refresh_image_list()
        self.wait_window(popup)

    def build_setting_tab(self):
        self.setting_round_var = tk.StringVar()
        self.setting_event_listbox = tk.Listbox(self.setting_frame, height=6)

        # 라운드 설정 필드
        round_frame = ttk.Frame(self.setting_frame, padding=10)
        round_frame.pack(fill='x')
        ttk.Label(round_frame, text="최대 장면").pack(side='left')
        ttk.Entry(round_frame, textvariable=self.setting_round_var).pack(side='left', padx=5)
        self.create_tooltip(round_frame, "몇 번의 장면이 나온 후 엔딩이 나올지를 결정합니다. 0일 경우, 무한으로 취급.")

        # 반복 이벤트 라벨
        ttk.Label(self.setting_frame, text="장면이 끝날 때마다 반복되는 이벤트").pack(anchor='w', pady=(10, 4))

        # 리스트와 버튼 프레임을 묶는 상위 프레임
        event_area = ttk.Frame(self.setting_frame)
        event_area.pack(fill='both', expand=True)

        # 이벤트 리스트박스
        event_scroll = ttk.Scrollbar(event_area, orient='vertical')
        self.setting_event_listbox = tk.Listbox(event_area, height=6, yscrollcommand=event_scroll.set)
        event_scroll.config(command=self.setting_event_listbox.yview)

        self.setting_event_listbox.pack(side='left', fill='both', expand=True)
        self.setting_event_listbox.bind("<Double-Button-1>", self.edit_setting_event)
        event_scroll.pack(side='left', fill='y')

        # 버튼 영역
        event_btns = ttk.Frame(event_area)
        event_btns.pack(side='left', padx=5)

        ttk.Button(event_btns, text="➕", command=self.add_setting_event).pack(pady=2)
        ttk.Button(event_btns, text="✏", command=self.edit_setting_event).pack(pady=2)
        ttk.Button(event_btns, text="❌", command=self.delete_setting_event).pack(pady=2)

    def refresh_setting_fields(self):
        round_val = str(self.setting_data.get("maxRound", 0))
        self.setting_round_var.set(round_val)

    def refresh_setting_event_list(self):
        self.setting_event_listbox.delete(0, tk.END)
        for ev in self.setting_data.get("events", []):
            desc = f"{ev.get('type', '')} → {ev.get('target', '')} {ev.get('operation', '')} {ev.get('value', '')}"
            if ev.get("condition"):
                desc += f" (조건: {ev['condition']})"
            self.setting_event_listbox.insert(tk.END, desc)

    def add_setting_event(self):
        events = self.setting_data.setdefault("events", [])
        self.open_event_editor("setting", "setting", events, index=None)
        self.refresh_setting_event_list()

    def edit_setting_event(self, event=None):
        sel = self.setting_event_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        events = self.setting_data.get("events", [])
        self.open_event_editor("setting", "setting", events, index=idx)
        self.refresh_setting_event_list()

    def delete_setting_event(self):
        sel = self.setting_event_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if messagebox.askyesno("삭제 확인", "이 이벤트를 삭제하시겠습니까?"):
            self.setting_data.get("events", []).pop(idx)
            self.refresh_setting_event_list()


    def on_combobox_selected(self, field, combo, input_var, input_entry, exists_var):
        selected_name = combo.get()

        if selected_name == "(직접 입력)":
            input_entry.config(state='normal')
            input_var.set(0)
        else:
            current_id = getattr(self, 'current_rid', None)
            if not current_id:
                return

            for rid in self.resource_ids:
                name = self.resource_data[rid].get("name", rid)
                if rid != current_id and name == selected_name:
                    input_var.set(rid)
                    break
            input_entry.config(state='disabled')

        self.update_current_resource()


    def update_maxmin_state(self):
        for field in ["maxValue", "minValue"]:
            exists_var, input_var, combo, input_entry = self.resource_fields[field]
            state = 'normal' if exists_var.get() else 'disabled'
            combo.config(state=state)
            input_entry.config(state=state if combo.get() == "(직접 입력)" else 'disabled')
        self.after_idle(self.update_current_resource)

    def load_resource_json(self):
        path = DATA_FILES["Resource"]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.resource_data = json.load(f)
            self.refresh_resource_list(select_index=0)
        except Exception as e:
            messagebox.showerror("불러오기 오류", str(e))

    def load_custom_json(self):
        path = DATA_FILES["Custom"]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.custom_data = json.load(f)
            self.refresh_custom_list(select_index=0)
        except Exception as e:
            messagebox.showerror("불러오기 오류", str(e))

    def load_scene_json(self):
        path = DATA_FILES["Scene"]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.scene_data = json.load(f)
            first_key = next(iter(self.scene_data), None)
            self.refresh_scene_list(selected_id=first_key)
        except Exception as e:
            messagebox.showerror("불러오기 오류", str(e))

    def load_endings_json(self):
        path = DATA_FILES["Endings"]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.endings_data = json.load(f)
            first_key = next(iter(self.endings_data), None)
            self.refresh_ending_list(selected_id=first_key)
        except Exception as e:
            messagebox.showerror("불러오기 오류", str(e))

    def load_setting_json(self):
        path = DATA_FILES["Setting"]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.setting_data = json.load(f)
            self.refresh_setting_fields()
            self.refresh_setting_event_list()
        except Exception as e:
            messagebox.showerror("불러오기 오류", str(e))


    def refresh_resource_list(self, select_index=None):
        self.resource_listbox.delete(0, tk.END)
        self.resource_ids = list(self.resource_data.keys())
        for rid in self.resource_ids:
            self.resource_listbox.insert(tk.END, f"{rid}")

        if self.resource_ids:
            if select_index is None:
                select_index = self.resource_listbox.curselection()
                if select_index:
                    select_index = select_index[0]
                else:
                    select_index = 0
            self.resource_listbox.select_set(select_index)
            self.on_resource_select()

    def refresh_custom_list(self, select_index=0):
        self.custom_listbox.delete(0, tk.END)
        self.custom_keys = list(self.custom_data.keys())
        for key in self.custom_keys:
            self.custom_listbox.insert(tk.END, f"{key}")
        if self.custom_keys:
            if select_index is None:
                select_index = self.custom_listbox.curselection()
                if select_index:
                    select_index = select_index[0]
                else:
                    select_index = 0
            self.custom_listbox.select_set(select_index)
            self.on_custom_category_select()

    def on_resource_select(self, event=None):
        selection = self.resource_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        rid = self.resource_ids[idx]
        self.current_rid = rid
        entry = self.resource_data[rid]

        self._suspend_update = True


        for key, var in self.resource_fields.items():
            if key in ["maxValue", "minValue"]:
                exists_var, input_var, combo, input_entry = var
                val = entry.get(key, None)
                exists_var.set(val is not None)
                input_var.set(str(val) if val is not None else "")
                others = [self.resource_data[r].get("name", r) for r in self.resource_ids if r != rid]
                combo['values'] = ["(직접 입력)"] + others
                matched_name = None
                for r in self.resource_ids:
                    if r != rid and r == val:
                        matched_name = self.resource_data[r].get("name", r)
                        break
                combo.set(matched_name if matched_name else "(직접 입력)")

                input_entry.config(state='normal' if combo.get() == "(직접 입력)" and exists_var.get() else 'disabled')
                combo.config(state='readonly' if exists_var.get() else 'disabled')
            elif isinstance(var, tk.BooleanVar):
                var.set(entry.get(key, True))
            else:
                var.set(str(entry.get(key, "")))

        self._suspend_update = False

        self.update_delete_button()

    def update_current_resource(self):
        if getattr(self, '_suspend_update', False):
            return
        rid = getattr(self, 'current_rid', None)
        if rid is None:
            print("[오류] current_rid 없음 — 저장 중단")
            return
        updated = {}
        for key, var in self.resource_fields.items():
            if key in ["maxValue", "minValue"]:
                exists_var, input_var, _, _ = var
                if exists_var.get():
                    val = input_var.get()
                    try:
                        val = int(val)
                    except:
                        pass
                    updated[key] = val
            elif isinstance(var, tk.BooleanVar):
                updated[key] = var.get()
            else:
                val = var.get()
                try:
                    val = int(val)
                except:
                    pass
                updated[key] = val
        updated["value"] = updated.get("realValue", "")
        self.resource_data[rid] = updated

        idx = self.resource_ids.index(rid)
        self.resource_listbox.delete(idx)
        self.resource_listbox.insert(idx, f"{rid}")
        self.resource_listbox.select_set(idx)

    def add_resource(self):
        def validate_id(new_id):
            if not new_id:
                return False, "ID를 입력하세요."
            if not new_id.isidentifier():
                return False, "ID는 영문자, 숫자, 밑줄(_)로 구성되어야 합니다."
            if new_id in self.resource_data:
                return False, "이미 존재하는 ID입니다."
            return True, ""

        popup = tk.Toplevel(self)
        popup.title("새 변수 ID")
        popup.resizable(False, False)

        popup.transient(self)
        popup.grab_set()

        popup.update_idletasks()
        width, height = 300, 150
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(popup, text="ID:").pack(pady=5)
        id_var = tk.StringVar()
        id_entry = ttk.Entry(popup, textvariable=id_var)
        id_entry.pack(pady=5)

        error_label = tk.Label(popup, text="", fg="red")
        error_label.pack()

        confirm_btn = ttk.Button(popup, text="확인", state='disabled')
        confirm_btn.pack(pady=5)

        def on_change(*args):
            valid, msg = validate_id(id_var.get())
            confirm_btn.config(state='normal' if valid else 'disabled')
            error_label.config(text=msg)

        id_var.trace_add('write', on_change)

        def on_confirm():
            new_id = id_var.get()
            self.resource_data[new_id] = {
                "name": f"변수 {len(self.resource_data)+1}",
                "realValue": 0,
                "value": 0,
                "show": True,
                "showIfPositive": False,
                "positive": True,
                "summary": True
            }
            popup.destroy()
            self.refresh_resource_list(select_index=len(self.resource_data)-1)

        confirm_btn.config(command=on_confirm)
        id_entry.focus_set()
        popup.wait_window()

    def delete_resource(self):
        if len(self.resource_ids) <= 1:
            return
        idx = self.resource_listbox.curselection()[0]
        rid = self.resource_ids[idx]
        name = self.resource_data[rid].get("name", rid)

        confirm = messagebox.askyesno("삭제 확인", f"[{name}] 변수를 삭제하시겠습니까?")
        if not confirm:
            return

        del self.resource_data[rid]
        new_index = max(0, idx - 1)
        self.refresh_resource_list(select_index=new_index)

    def update_delete_button(self):
        self.del_btn.config(state='normal' if len(self.resource_ids) > 1 else 'disabled')

    def move_resource_up(self):
        idx = self.resource_listbox.curselection()[0]
        if idx == 0:
            return
        self.resource_ids[idx], self.resource_ids[idx-1] = self.resource_ids[idx-1], self.resource_ids[idx]
        self.resource_data = {rid: self.resource_data[rid] for rid in self.resource_ids}
        self.refresh_resource_list(select_index=idx - 1)

    def move_resource_down(self):
        idx = self.resource_listbox.curselection()[0]
        if idx >= len(self.resource_ids) - 1:
            return
        self.resource_ids[idx], self.resource_ids[idx+1] = self.resource_ids[idx+1], self.resource_ids[idx]
        self.resource_data = {rid: self.resource_data[rid] for rid in self.resource_ids}
        self.refresh_resource_list(select_index=idx + 1)

    def move_custom_up(self):
        selection = self.custom_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        idx = selection[0]
        self.custom_keys[idx - 1], self.custom_keys[idx] = self.custom_keys[idx], self.custom_keys[idx - 1]
        self.custom_data = {k: self.custom_data[k] for k in self.custom_keys}
        self.refresh_custom_list(select_index=idx - 1)

    def move_custom_down(self):
        selection = self.custom_listbox.curselection()
        if not selection or selection[0] >= len(self.custom_keys) - 1:
            return
        idx = selection[0]
        self.custom_keys[idx + 1], self.custom_keys[idx] = self.custom_keys[idx], self.custom_keys[idx + 1]
        self.custom_data = {k: self.custom_data[k] for k in self.custom_keys}
        self.refresh_custom_list(select_index=idx + 1)

    def create_tooltip(self, widget, text):
        def on_enter(event):
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(
                self.tooltip,
                text=text,
                background="#f0f0f0",
                relief='solid',
                borderwidth=1,
                wraplength=300,
                font=("맑은 고딕", 9)
            )
            label.pack()

        def on_leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                del self.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


    def save_data_json(self):
        try:
            def full_path(key):
                return os.path.join(self.base_path, DATA_FILES[key])

            with open(full_path("Resource"), 'w', encoding='utf-8') as f:
                json.dump(self.resource_data, f, indent=4, ensure_ascii=False)
            with open(full_path("Custom"), 'w', encoding='utf-8') as f:
                json.dump(self.custom_data, f, indent=4, ensure_ascii=False)
            with open(full_path("Scene"), 'w', encoding='utf-8') as f:
                json.dump(self.scene_data, f, indent=4, ensure_ascii=False)
            with open(full_path("Endings"), 'w', encoding='utf-8') as f:
                json.dump(self.endings_data, f, indent=4, ensure_ascii=False)
            with open(full_path("Setting"), 'w', encoding='utf-8') as f:
                self.setting_data["maxRound"] = int(self.setting_round_var.get()) if self.setting_round_var.get().isdigit() else 0
                json.dump(self.setting_data, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("저장 완료", "모든 데이터가 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))


    def build_and_run(self):
        self.save_data_json()

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        def run_server():
            os.chdir(base_path)
            try:
                server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
                print("[서버 시작] http://localhost:8000")
                server.serve_forever()
            except Exception as e:
                print("[서버 오류]", e)

        threading.Thread(target=run_server, daemon=True).start()
        webbrowser.open('http://localhost:8000/index.html')


if __name__ == "__main__":
    app = JSONEditor()
    app.mainloop()
