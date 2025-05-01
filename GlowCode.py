import tkinter as tk
from tkinter import messagebox, Menu
import ctypes
import re
import os
import time
import platform
import sys
import customtkinter as ctk
from customtkinter import filedialog

if platform.system() == 'Windows':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except:
        pass

class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(
            bg='#1e1e1e',
            fg='#d4d4d4',
            font=('Consolas', 12),
            selectbackground='#264f78',
            selectforeground='#ffffff',
            inactiveselectbackground='#264f78'
        )

        self._orig = str(self) + "_orig"
        self.tk.call("rename", str(self), self._orig)
        self.tk.createcommand(str(self), self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")

        return result

class Editor:
    def __init__(self, parent):
        self._in_sync = False

        tmp = tk.Label()
        fg_color = tmp.cget("foreground")
        bg_color = tmp.cget("background")
        tmp.destroy()

        self.w = tk.Frame(parent, bg='#1e1e1e')
        self.w.pack(fill=tk.BOTH, expand=True)

        self.hs = ctk.CTkScrollbar(self.w, orientation=tk.HORIZONTAL,
                                   button_color='#3e3e40', button_hover_color='#4d4d4d')
        self.vs = ctk.CTkScrollbar(self.w, button_color='#3e3e40', button_hover_color='#4d4d4d')

        self.ruler = tk.Text(
            self.w,
            bg='#1e1e1e',
            fg='#d4d4d4',
            wrap=tk.NONE,
            relief=tk.FLAT,
            width=4,
            cursor="arrow",
            selectborderwidth=0,
            exportselection=0,
            font=('Consolas', 12),
            highlightthickness=0
        )

        self.editor = CustomText(
            self.w,
            wrap=tk.NONE,
            exportselection=1,
            insertwidth=2,
            xscrollcommand=self.hs.set,
            insertbackground='white',
            bg='#1e1e1e',
            highlightthickness=0,
            padx=5,
            pady=3
        )

        self.editor.bind("<<TextModified>>", self.rulersync)

        self.hs.configure(command=self.editor.xview)
        self.vs.configure(command=self.scrollsync)
        self.ruler.configure(yscrollcommand=lambda *args: self.edsync(self.editor, self.ruler, *args))
        self.editor.configure(yscrollcommand=lambda *args: self.edsync(self.ruler, self.editor, *args))

        self.ruler.tag_configure("right", justify=tk.RIGHT)
        self.ruler.insert(tk.END, "1", "right")
        self.ruler.configure(state=tk.DISABLED)

        self.w.grid_rowconfigure(0, weight=1, minsize=0)
        self.w.grid_columnconfigure(1, weight=1, minsize=0)

        self.editor.grid(padx=2, pady=0, row=0, column=1, sticky="news")
        self.ruler.grid(padx=2, pady=0, row=0, column=0, sticky="nws")
        self.vs.grid(padx=1, pady=0, row=0, column=2, sticky="news")
        self.hs.grid(padx=0, pady=1, row=1, column=1, sticky="news")

    def scrollsync(self, *args):
        self.editor.yview(*args)
        self.ruler.yview_moveto(self.editor.yview()[0])

    def edsync(self, tw, sw, *args):
        if not self._in_sync:
            self._in_sync = True
            tw.yview_moveto(sw.yview()[0])
            self.w.update_idletasks()
            self.vs.set(*args)
            self._in_sync = False

    def rulersync(self, *args):
        elines = int(self.editor.index(tk.END).split(".")[0]) - 1
        rlines = int(self.ruler.index(tk.END).split(".")[0]) - 1
        if rlines != elines:
            self.ruler.configure(state=tk.NORMAL)
            if rlines < elines:
                for i in range(rlines + 1, elines + 1):
                    self.ruler.insert(tk.END, f"\n{i}", "right")
            else:
                self.ruler.delete(f"{elines + 1}.0 -1chars", tk.END)
            self.ruler.configure(state=tk.DISABLED)
            self.ruler.yview_moveto(self.editor.yview()[0])
            self.w.update_idletasks()

class CodeEditor:
    def __init__(self, root, file_path=None):
        self.root = root
        self.root.title("GlowCode | ")
        self.root.geometry('1000x700')
        self.root.configure(bg='#1e1e1e')
        self.current_file = None
        self.file_extension = '.py'

        self.start_time = time.time()
        self.update_title()
        self.root.after(1000, self.update_title)

        self.file_types = {
            '.py': {
                'keywords': ['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
                             'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global',
                             'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
                             'try', 'while', 'with', 'yield', 'print', 'input'],
                'comments': '#.*?$',
                'strings': ['".*?"', "'.*?'"],
                'functions': r'\bdef\s+(\w+)\s*$$|\bclass\s+(\w+)',
                'numbers': r'\b\d+\b'
            },
            '.html': {
                'tags': r'<\/?\w+.*?>',
                'attributes': r'\b\w+=',
                'comments': r'<!--.*?-->',
                'doctype': r'<!DOCTYPE.*?>',
                'scripts': r'<script.*?>.*?</script>',
                'styles': r'<style.*?>.*?</style>'
            },
            '.asm': {
                'instructions': r'\b(mov|add|sub|mul|div|jmp|call|ret|push|pop|cmp|je|jne|jg|jl|jge|jle|loop|xor|or|and|not|shl|shr|inc|dec|nop)\b',
                'registers': r'\b(e?[a-d]x|e?[s-d]i|e?[s-b]p|e?ip|r[0-9]{1,2}d?|xmm[0-9]+|ymm[0-9]+|zmm[0-9]+)\b',
                'directives': r'\.(data|text|global|extern|section|byte|word|dword|qword|resb|resw|resd|resq|equ|times|db|dw|dd|dq)\b',
                'comments': r';.*?$',
                'numbers': r'\b[0-9]+[h]?\b',
                'strings': ['".*?"', "'.*?'"]
            },
            '.cpp': {
                'keywords': ['alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor',
                             'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t',
                             'class', 'compl', 'concept', 'const', 'consteval', 'constexpr', 'const_cast',
                             'continue', 'co_await', 'co_return', 'co_yield', 'decltype', 'default', 'delete',
                             'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit', 'export', 'extern',
                             'false', 'float', 'for', 'friend', 'goto', 'if', 'inline', '#include', 'int', 'long',
                             'mutable', 'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator',
                             'or', 'or_eq', 'private', 'protected', 'public', 'register', 'reinterpret_cast',
                             'requires', 'return', 'short', 'signed', 'sizeof', 'static', 'static_assert',
                             'static_cast', 'struct', 'switch', 'template', 'this', 'thread_local', 'throw',
                             'true', 'try', 'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using',
                             'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq'],
                'comments': r'//.*?$|/\*.*?\*/',
                'strings': ['".*?"', "'.*?'", r'R"$$.*?$$"'],
                'functions': r'\b\w+\s+\w+\s*$$[^)]*$$\s*(?=\{)|class\s+\w+',
                'numbers': r'\b\d+\b',
                'preprocessor': r'#.*?$'
            },
            '.c': {
                'keywords': ['auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double',
                             'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int', 'long', 'register',
                             'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef',
                             'union', 'unsigned', 'void', 'volatile', 'while'],
                'comments': r'//.*?$|/\*.*?\*/',
                'strings': ['".*?"', "'.*?'"],
                'functions': r'\b\w+\s+\w+\s*$$[^)]*$$\s*(?=\{)|struct\s+\w+',
                'numbers': r'\b\d+\b',
                'preprocessor': r'#.*?$'
            },
            '.h': {
                'keywords': ['auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double',
                             'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int', 'long', 'register',
                             'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef',
                             'union', 'unsigned', 'void', 'volatile', 'while'],
                'comments': r'//.*?$|/\*.*?\*/',
                'strings': ['".*?"', "'.*?'"],
                'functions': r'\b\w+\s+\w+\s*$$[^)]*$$\s*(?=\{)|struct\s+\w+',
                'numbers': r'\b\d+\b',
                'preprocessor': r'#.*?$'
            },
            '.b': {
                'keywords': [
                    'auto', 'extrn', 'if', 'else', 'while', 'repeat', 'do', 'for', 
                    'switch', 'case', 'default', 'break', 'next', 'return', 'goto'],
                'comments': r'/\*.*?\*/',
                'strings': ['".*?"'],
                'functions': r'\b\w+\s*\(\s*.*?\s*\)\s*\{',
                'numbers': r'\b\d+\b|\b0[0-7]+\b|\b\d+\.\d+([eE][+-]?\d+)?\b',
                'operators': r'\+|\-|\*|\/|\%|\=|\==|\!=|\<|\>|\<=|\>=|\&\&|\|\||\&|\||\~|\<<|\>>|\+\+|\--'
            },
            '.css': {
                'selectors': r'[^{}]*\{',
                'properties': r'(\b[\w-]+\b)(?=\s*:)',
                'values': r':\s*([^;]+)',
                'comments': r'/\*.*?\*/',
                'units': r'\b\d+(px|em|rem|%|vw|vh|vmin|vmax)\b',
                'colors': r'#[0-9a-fA-F]{3,6}|\b(rgb|hsl)a?$$[^)]*$$',
                'important': r'!\s*important'
            },
            '.js': {
                'keywords': ['break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default',
                             'delete', 'do', 'else', 'export', 'extends', 'finally', 'for', 'function', 'if',
                             'import', 'in', 'instanceof', 'new', 'return', 'super', 'switch', 'this', 'throw',
                             'try', 'typeof', 'var', 'void', 'while', 'with', 'yield', 'let', 'await', 'async'],
                'comments': r'//.*?$|/\*.*?\*/',
                'strings': ['".*?"', "'.*?'", '`.*?`'],
                'functions': r'\bfunction\s+\w+\s*$$[^)]*$$|\b\w+\s*$$[^)]*$$\s*(?=>|\{)|class\s+\w+',
                'numbers': r'\b\d+\b',
                'regex': r'/[^/\n]*(?:\\.[^/\n]*)*/[gimyus]*',
                'template_literals': r'\$\{[^}]*\}'
            },
            '.sh': {
                'shebang': r'^#!.*$',
                'keywords': ['if', 'then', 'else', 'elif', 'fi', 'case', 'esac', 'for', 'while', 'until', 'do',
                             'done', 'in', 'function', 'select', 'time', 'export', 'local', 'readonly'],
                'comments': r'#.*?$',
                'strings': ['".*?"', "'.*?'", '`.*?`', '\$$$.*?$$'],
                'functions': r'\w+\s*$$\s*$$\s*\{',
                'variables': r'\$\w+',
                'parameters': r'\$[0-9]',
                'operators': r'&&|\|\||>>|<<|>|<|&|\|'
            },
            '.ps1': {
                'keywords': ['begin', 'break', 'catch', 'class', 'continue', 'data', 'define', 'do', 'dynamicparam',
                             'else', 'elseif', 'end', 'exit', 'filter', 'finally', 'for', 'foreach', 'from', 'function',
                             'if', 'in', 'param', 'process', 'return', 'switch', 'throw', 'trap', 'try', 'until',
                             'using', 'var', 'while', 'workflow'],
                'comments': r'#.*?$|<#.*?#>',
                'strings': ['".*?"', "'.*?'", '@".*?"', "@'.*?'"],
                'functions': r'function\s+\w+|\w+\s*-[a-zA-Z]+\s+',
                'variables': r'\$\w+',
                'parameters': r'-\w+',
                'cmdlets': r'\w+-[a-zA-Z]+\b',
                'operators': r'-eq|-ne|-gt|-ge|-lt|-le|-like|-notlike|-match|-notmatch|-contains|-notcontains|-in|-notin|-replace'
            },
            '.bat': {
                'keywords': ['begin', 'break', 'catch', 'class', 'continue', 'data', 'define', 'do', 'dynamicparam',
                             'else', 'elseif', 'end', 'exit', 'filter', 'finally', 'for', 'foreach', 'from', 'function',
                             'if', 'in', 'param', 'process', 'return', 'switch', 'throw', 'trap', 'try', 'until',
                             'using', 'var', 'while', 'workflow'],
                'comments': r'#.*?$|<#.*?#>',
                'strings': ['".*?"', "'.*?'", '@".*?"', "@'.*?'"],
                'functions': r'function\s+\w+|\w+\s*-[a-zA-Z]+\s+',
                'variables': r'\$\w+',
                'parameters': r'-\w+',
                'cmdlets': r'\w+-[a-zA-Z]+\b',
                'operators': r'-eq|-ne|-gt|-ge|-lt|-le|-like|-notlike|-match|-notmatch|-contains|-notcontains|-in|-notin|-replace'
            },
            '.md': {
                'headers': r'^#+.*$',
                'bold': r'\*\*.*?\*\*|__.*?__',
                'italic': r'\*.*?\*|_.*?_',
                'code': r'`.*?`',
                'code_blocks': r'```.*?```',
                'links': r'$$.*?$$$$.*?$$',
                'images': r'!$$.*?$$$$.*?$$',
                'lists': r'^(\s*[-*+]|\s*\d+\.)\s+',
                'blockquotes': r'^>.*$',
                'horizontal_rules': r'^---|^\*\*\*|^___'
            },
            '.bas': {
                'keywords': ['DIM', 'GOTO', 'IF', 'THEN', 'ELSE', 'END', 'FOR', 'TO', 'NEXT', 'WHILE', 'WEND', 'PRINT', 'INPUT', 'REM', 'LET', 'DEF', 'SUB', 'FUNCTION'],
                'comments': r'\'[^\n]*$',
                'strings': ['".*?"', "'.*?'"]
            },
            '.hc': {
                'keywords': ['auto', 'break', 'case', 'continue', 'default', 'do', 'else', 'for', 'if', 'return', 'switch', 'while', 'func', 'var', 'const', 'struct', 'namespace', 'enum', 'public', 'private', 'protected', 'static', 'inline', 'sizeof', 'typedef', 'new', 'delete', 'try', 'catch', 'throw', 'using'],
                'comments': r'//.*?$|/\*.*?\*/',
                'strings': ['".*?"', "'.*?'"]
            },
            '.rs': {
                'keywords': ['as', 'break', 'const', 'continue', 'crate', 'else', 'enum', 'extern', 'false', 'fn', 'for', 'if', 'impl', 'in', 'let', 'loop', 'match', 'mod', 'move', 'mut', 'pub', 'ref', 'return', 'Self', 'self', 'static', 'struct', 'trait', 'true', 'type', 'unsafe', 'use', 'where', 'while', 'async', 'await', 'dyn', 'abstract', 'become', 'box', 'do', 'final', 'macro', 'override', 'priv', 'typeof', 'unsized', 'virtual', 'yield', 'try'],
                'comments': r'//.*?$|/\*.*?\*/',
                'strings': ['".*?"', "'.*?'"]
            },
            '.dart': {
                'keywords': ['abstract', 'as', 'assert', 'async', 'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'covariant', 'default', 'deferred', 'do', 'else', 'enum', 'export', 'extension', 'external', 'factory', 'false', 'final', 'finally', 'for', 'if', 'implements', 'import', 'in', 'interface', 'is', 'late', 'library', 'mixin', 'new', 'null', 'on', 'operator', 'part', 'rethrow', 'return', 'static', 'super', 'switch', 'this', 'throw', 'true', 'try', 'typedef', 'var', 'void', 'while', 'with', 'yield', 'enum', 'const', 'final', 'var', 'dynamic', 'typedef', 'set', 'get', 'abstract', 'extension', 'covariant', 'static', 'async', 'await', 'sync'],
                'comments': r'//.*?$|/\*.*?\*/',
                'strings': ['".*?"', "'.*?'", r'R"$$.*?$$"']
            }
        }

        self.colors = {
            'keywords': "#cc7832",
            'comments': "#808080",
            'strings': "#6a8759",
            'functions': "#ffc66d",
            'numbers': "#6897bb",
            'tags': "#e8bf6a",
            'attributes': "#9876aa",
            'doctype': "#bbb529",
            'scripts': "#6a8759",
            'styles': "#6a8759",
            'instructions': "#cc7832",
            'registers': "#94558d",
            'directives': "#bbb529",
            'preprocessor': "#cc7832",
            'selectors': "#e8bf6a",
            'properties': "#9876aa",
            'values': "#a9b7c6",
            'units': "#6897bb",
            'colors': "#6a8759",
            'important': "#cc7832",
            'regex': "#6a8759",
            'template_literals': "#6a8759",
            'shebang': "#808080",
            'variables': "#94558d",
            'parameters': "#6897bb",
            'operators': "#cc7832",
            'cmdlets': "#ffc66d",
            'headers': "#ffc66d",
            'bold': "#cc7832",
            'italic': "#a9b7c6",
            'code': "#6a8759",
            'code_blocks': "#6a8759",
            'links': "#6897bb",
            'images': "#6897bb",
            'lists': "#a9b7c6",
            'blockquotes': "#808080",
            'horizontal_rules': "#808080"
        }

        self.setup_ui()
        self.previous_text = ""

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.editor_frame.editor.delete('1.0', "end")
                self.editor_frame.editor.insert('1.0', content)
                self.current_file = file_path
                self.file_extension = os.path.splitext(file_path)[1].lower()
                self.root.title(f"GlowCode | {os.path.basename(file_path)}")
                self.highlight_syntax()
                self.update_line_numbers()
                self.highlight_current_line()
        except FileNotFoundError:
            self.current_file = file_path
            self.file_extension = os.path.splitext(file_path)[1].lower()
            self.root.title(f"GlowCode | {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def setup_ui(self):
        menubar = Menu(self.root, bg='#252526', fg='#d4d4d4', activebackground='#3e3e40', activeforeground='#ffffff')

        file_menu = Menu(menubar, tearoff=0, bg='#252526', fg='#d4d4d4', activebackground='#3e3e40', activeforeground='#ffffff')
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        info_menu = Menu(menubar, tearoff=0, bg='#252526', fg='#d4d4d4', activebackground='#3e3e40', activeforeground='#ffffff')
        info_menu.add_command(label="Info", command=self.show_info)
        menubar.add_cascade(label="About", menu=info_menu)

        self.root.config(menu=menubar)

        self.editor_frame = Editor(self.root)

        self.editor_frame.editor.tag_configure('current_line', background='#2d2d2d')

        self.status_bar = ctk.CTkLabel(
            self.root,
            text="Ln 1, Col 1  {} Python",
            anchor='w',
            font=('Consolas', 15),
            text_color='#858585'
        )
        self.status_bar.pack(side='bottom', fill='x')

        self.configure_tags()

        self.root.bind('<Control-s>', lambda event: self.save_file())
        self.root.bind('<Control-o>', lambda event: self.open_file())
        self.root.bind('<Control-n>', lambda event: self.new_file())
        self.root.bind('<Control-Shift-S>', lambda event: self.save_as_file())

        self.editor_frame.editor.bind('<KeyRelease>', self.on_text_changed)
        self.editor_frame.editor.bind('<Button-1>', self.update_cursor_position)
        self.editor_frame.editor.bind('<Key>', self.update_cursor_position)
        self.editor_frame.editor.bind('<Motion>', self.update_cursor_position)

        self.editor_frame.editor.bind('<<TextModified>>', self.highlight_current_line)
        self.editor_frame.editor.bind('<Configure>', self.highlight_current_line)

        self.highlight_current_line()
        self.update_line_numbers()

    def highlight_current_line(self, event=None):
        self.editor_frame.editor.tag_remove('current_line', '1.0', 'end')
        cursor_position = self.editor_frame.editor.index(tk.INSERT)
        line_number = cursor_position.split('.')[0]
        start = f'{line_number}.0'
        end = f'{line_number}.0 lineend +1c'
        self.editor_frame.editor.tag_add('current_line', start, end)

    def configure_tags(self):
        for tag in self.colors:
            self.editor_frame.editor.tag_configure(tag, foreground=self.colors[tag])

    def on_text_changed(self, event=None):
        self.update_line_numbers()
        self.highlight_syntax()
        self.highlight_current_line()

    def update_line_numbers(self, event=None):
        self.editor_frame.rulersync()
        self.update_cursor_position()

    def update_cursor_position(self, event=None):
        cursor_pos = self.editor_frame.editor.index(tk.INSERT)
        line, column = cursor_pos.split('.')
        lang_name = self.get_language_name_by_extension(self.file_extension)
        self.status_bar.configure(text=f"Ln {line}, Col {column}  {{}} {lang_name}")
        self.highlight_current_line()

    def get_language_name_by_extension(self, extension):
        ext = extension.lower()
        extension_to_language = {
            '.py': 'Python',
            '.pyw': 'Python',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.asm': 'Assembly',
            '.s': 'Assembly',
            '.cpp': 'C++',
            '.cc': 'C++',
            '.cxx': 'C++',
            '.h': 'C',
            '.hpp': 'C++',
            '.c': 'C',
            '.b': 'B',
            '.css': 'CSS',
            '.js': 'JavaScript',
            '.sh': 'Bash',
            '.bat': 'Batch',
            '.ps1': 'PowerShell',
            '.md': 'Markdown',
            '.bas': 'BASIC',
            '.hc': 'HolyC',
            '.rs': 'Rust',
            '.dart': 'Dart'
        }
        return extension_to_language.get(ext, 'Unknown')

    def new_file(self):
        self.editor_frame.editor.delete('1.0', "end")
        self.current_file = None
        self.file_extension = '.py'
        self.root.title("GlowCode | ")
        self.update_line_numbers()
        self.highlight_syntax()
        self.highlight_current_line()

    def open_file(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("All files", "*.*"),
                    ("Python files", "*.py"),
                    ("HTML files", "*.html"),
                    ("CSS files", "*.css"),
                    ("JavaScript files", "*.js"),
                    ("Assembly files", "*.asm"),
                    ("C++ files", "*.cpp"),
                    ("C files", "*.c *.h"),
                    ("B files", "*.b"),
                    ("Bash scripts", "*.sh"),
                    ("PowerShell scripts", "*.ps1 *.bat"),
                    ("Markdown files", "*.md"),
                    ("BASIC files", "*.bas"),
                    ("HolyC files", "*.hc"),
                    ("Rust files", "*.rs"),
                    ("Dart files", "*.dart")
                ]
            )
        if file_path:
            self.load_file(file_path)

    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(self.editor_frame.editor.get('1.0', "end-1c"))
                messagebox.showinfo("Успех", "Файл успешно сохранен")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
        else:
            self.save_as_file()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[
                    ("All files", "*.*"),
                    ("Python files", "*.py"),
                    ("HTML files", "*.html"),
                    ("CSS files", "*.css"),
                    ("JavaScript files", "*.js"),
                    ("Assembly files", "*.asm"),
                    ("C++ files", "*.cpp"),
                    ("C files", "*.c *.h"),
                    ("B files", "*.b"),
                    ("Bash scripts", "*.sh"),
                    ("PowerShell scripts", "*.ps1 *.bat"),
                    ("Markdown files", "*.md"),
                    ("BASIC files", "*.bas"),
                    ("HolyC files", "*.hc"),
                    ("Rust files", "*.rs"),
                    ("Dart files", "*.dart")
                ]
        )
        if file_path:
            self.current_file = file_path
            self.file_extension = os.path.splitext(file_path)[1].lower()
            self.load_file(file_path)
            self.root.title(f"GlowCode | {os.path.basename(file_path)}")

    def highlight_syntax(self):
        current_text = self.editor_frame.editor.get('1.0', "end-1c")
        if current_text == self.previous_text:
            return
        for tag in self.editor_frame.editor.tag_names():
            if tag != 'current_line':
                self.editor_frame.editor.tag_remove(tag, "1.0", "end")
        syntax_rules = self.file_types.get(self.file_extension, self.file_types['.py'])
        self.apply_highlighting(syntax_rules)
        self.previous_text = current_text

    def apply_highlighting(self, syntax_rules):
        if 'keywords' in syntax_rules:
            for keyword in syntax_rules['keywords']:
                self.highlight_pattern(rf'\b{keyword}\b', 'keywords')
        if 'comments' in syntax_rules:
            self.highlight_pattern(syntax_rules['comments'], 'comments', multiline=True)
        if 'strings' in syntax_rules:
            for pattern in syntax_rules['strings']:
                self.highlight_pattern(pattern, 'strings')
        if 'functions' in syntax_rules:
            self.highlight_pattern(syntax_rules['functions'], 'functions')
        if 'numbers' in syntax_rules:
            self.highlight_pattern(syntax_rules['numbers'], 'numbers')
        if 'tags' in syntax_rules:
            self.highlight_pattern(syntax_rules['tags'], 'tags')
        if 'attributes' in syntax_rules:
            self.highlight_pattern(syntax_rules['attributes'], 'attributes')
        if 'doctype' in syntax_rules:
            self.highlight_pattern(syntax_rules['doctype'], 'doctype')
        if 'scripts' in syntax_rules:
            self.highlight_pattern(syntax_rules['scripts'], 'scripts')
        if 'styles' in syntax_rules:
            self.highlight_pattern(syntax_rules['styles'], 'styles')
        if 'instructions' in syntax_rules:
            self.highlight_pattern(syntax_rules['instructions'], 'instructions')
        if 'registers' in syntax_rules:
            self.highlight_pattern(syntax_rules['registers'], 'registers')
        if 'directives' in syntax_rules:
            self.highlight_pattern(syntax_rules['directives'], 'directives')
        if 'preprocessor' in syntax_rules:
            self.highlight_pattern(syntax_rules['preprocessor'], 'preprocessor')
        if 'selectors' in syntax_rules:
            self.highlight_pattern(syntax_rules['selectors'], 'selectors')
        if 'properties' in syntax_rules:
            self.highlight_pattern(syntax_rules['properties'], 'properties')
        if 'values' in syntax_rules:
            self.highlight_pattern(syntax_rules['values'], 'values')
        if 'units' in syntax_rules:
            self.highlight_pattern(syntax_rules['units'], 'units')
        if 'colors' in syntax_rules:
            self.highlight_pattern(syntax_rules['colors'], 'colors')
        if 'important' in syntax_rules:
            self.highlight_pattern(syntax_rules['important'], 'important')
        if 'regex' in syntax_rules:
            self.highlight_pattern(syntax_rules['regex'], 'regex')
        if 'template_literals' in syntax_rules:
            self.highlight_pattern(syntax_rules['template_literals'], 'template_literals')
        if 'shebang' in syntax_rules:
            self.highlight_pattern(syntax_rules['shebang'], 'shebang')
        if 'variables' in syntax_rules:
            self.highlight_pattern(syntax_rules['variables'], 'variables')
        if 'parameters' in syntax_rules:
            self.highlight_pattern(syntax_rules['parameters'], 'parameters')
        if 'operators' in syntax_rules:
            self.highlight_pattern(syntax_rules['operators'], 'operators')
        if 'cmdlets' in syntax_rules:
            self.highlight_pattern(syntax_rules['cmdlets'], 'cmdlets')
        if 'headers' in syntax_rules:
            self.highlight_pattern(syntax_rules['headers'], 'headers')
        if 'bold' in syntax_rules:
            self.highlight_pattern(syntax_rules['bold'], 'bold')
        if 'italic' in syntax_rules:
            self.highlight_pattern(syntax_rules['italic'], 'italic')
        if 'code' in syntax_rules:
            self.highlight_pattern(syntax_rules['code'], 'code')
        if 'code_blocks' in syntax_rules:
            self.highlight_pattern(syntax_rules['code_blocks'], 'code_blocks')
        if 'links' in syntax_rules:
            self.highlight_pattern(syntax_rules['links'], 'links')
        if 'images' in syntax_rules:
            self.highlight_pattern(syntax_rules['images'], 'images')
        if 'lists' in syntax_rules:
            self.highlight_pattern(syntax_rules['lists'], 'lists')
        if 'blockquotes' in syntax_rules:
            self.highlight_pattern(syntax_rules['blockquotes'], 'blockquotes')
        if 'horizontal_rules' in syntax_rules:
            self.highlight_pattern(syntax_rules['horizontal_rules'], 'horizontal_rules')

    def highlight_pattern(self, pattern, tag_name, multiline=False):
        text_content = self.editor_frame.editor.get('1.0', "end-1c")
        flags = re.MULTILINE | re.DOTALL if multiline else 0
        try:
            for match in re.finditer(pattern, text_content, flags):
                start = f"1.0 + {match.start()}c"
                end = f"1.0 + {match.end()}c"
                self.editor_frame.editor.tag_add(tag_name, start, end)
        except re.error:
            pass

    def update_title(self):
        elapsed_time = time.time() - self.start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        time_string = f"{minutes:02}:{seconds:02}"
        self.root.title(f"GlowCode | {time_string}")
        self.root.after(1000, self.update_title)

    def show_info(self):
        info_window = ctk.CTkToplevel(self.root)
        info_window.title("About")
        info_window.geometry("420x380")
        info_window.resizable(False, False)

        info_text = ctk.CTkLabel(
            info_window,
            text="GlowCode",
            font=('Consolas', 25)
        )
        info_text.pack(pady=5)

        info_text1 = ctk.CTkLabel(
            info_window,
            text="""
GlowCode is a text editor with syntax highlighting
for various programming and markup languages.
""",
            font=('Consolas', 12),
            justify='center'
        )
        info_text1.pack(pady=5, padx=10)

        info_text2 = ctk.CTkLabel(
            info_window,
            text="Supported languages",
            font=('Consolas', 25),
            justify='center'
        )
        info_text2.pack(pady=5, padx=10)

        info_text3 = ctk.CTkLabel(
            info_window,
            text="""

Python, HTML, CSS, JavaScript
C, B, C++, HolyC, Rust
Assembly, BASIC, Dart
Bash, PowerShell, Markdown
""",
            font=('Consolas', 12),
            justify='center'
        )
        info_text3.pack(pady=5, padx=10)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    ico_path = os.path.join(os.path.dirname(sys.argv[0]), "glowcode.ico")
    if os.path.exists(ico_path):
        if platform.system() == 'Windows':
            root.iconbitmap(ico_path)
        elif platform.system() == 'Linux':
            try:
                root.iconphoto(True, tk.PhotoImage(file=os.path.join(os.path.dirname(sys.argv[0]), "glowcode.png")))
            except Exception:
                pass
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    editor = CodeEditor(root, file_path)
    root.mainloop()