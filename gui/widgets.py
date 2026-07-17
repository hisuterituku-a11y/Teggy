"""
Переиспользуемые виджеты GUI с копипастом через keycode.
"""

import tkinter as tk
import customtkinter as ctk


class ClippableEntry(ctk.CTkEntry):
    """Поле ввода с поддержкой Ctrl+C/V/X/A и ПКМ."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Контекстное меню (ПКМ)
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Вырезать", command=self.cut_text)
        self.menu.add_command(label="Копировать", command=self.copy_text)
        self.menu.add_command(label="Вставить", command=self.paste_text)
        self.menu.add_separator()
        self.menu.add_command(label="Выделить всё", command=self.select_all)

        self.bind("<Button-3>", self.show_menu)

        # Горячие клавиши через keycode (работает на любой раскладке)
        self.bind("<Control-KeyPress>", self.control_keys)

    def show_menu(self, event):
        self.focus_force()
        self.menu.tk_popup(event.x_root, event.y_root)

    def control_keys(self, event):
        """Обрабатывает Ctrl+клавиша через keycode."""
        if event.keycode == 67:      # C
            self.copy_text()
        elif event.keycode == 86:    # V
            self.paste_text()
        elif event.keycode == 88:    # X
            self.cut_text()
        elif event.keycode == 65:    # A
            self.select_all()
        return "break"

    def copy_text(self):
        try:
            text = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except:
            pass

    def paste_text(self):
        try:
            text = self.clipboard_get()
            self.insert(tk.INSERT, text)
        except:
            pass

    def cut_text(self):
        self.copy_text()
        try:
            self.delete("sel.first", "sel.last")
        except:
            pass

    def select_all(self):
        self.select_range(0, tk.END)
        self.icursor(tk.END)
        return "break"


class ClippableTextbox(ctk.CTkTextbox):
    """Многострочное поле с поддержкой Ctrl+C/V/X/A и ПКМ."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Контекстное меню (ПКМ)
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Вырезать", command=self.cut_text)
        self.menu.add_command(label="Копировать", command=self.copy_text)
        self.menu.add_command(label="Вставить", command=self.paste_text)
        self.menu.add_separator()
        self.menu.add_command(label="Выделить всё", command=self.select_all)

        self.bind("<Button-3>", self.show_menu)

        # Горячие клавиши через keycode (работает на любой раскладке)
        self.bind("<Control-KeyPress>", self.control_keys)

    def show_menu(self, event):
        self.focus_force()
        self.menu.tk_popup(event.x_root, event.y_root)

    def control_keys(self, event):
        """Обрабатывает Ctrl+клавиша через keycode."""
        if event.keycode == 67:      # C
            self.copy_text()
        elif event.keycode == 86:    # V
            self.paste_text()
        elif event.keycode == 88:    # X
            self.cut_text()
        elif event.keycode == 65:    # A
            self.select_all()
        return "break"

    def copy_text(self):
        try:
            text = self.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except:
            pass

    def paste_text(self):
        try:
            text = self.clipboard_get()
            self.insert("insert", text)
        except:
            pass

    def cut_text(self):
        self.copy_text()
        try:
            self.delete("sel.first", "sel.last")
        except:
            pass

    def select_all(self):
        self.tag_add("sel", "1.0", "end-1c")
        self.mark_set("insert", "1.0")
        self.see("insert")
        return "break"