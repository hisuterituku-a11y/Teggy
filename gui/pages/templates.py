"""
Страница управления шаблонами.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from gui.theme.manager import ThemeManager

from gui.widgets import ClippableEntry, ClippableTextbox
from core.template_manager import TemplateManager
from core.exceptions import TemplateError


class TemplatesPage(ctk.CTkFrame):
    """Страница управления шаблонами."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.current_template = None

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self,
            text="📋 Шаблоны",
            font=("Arial", 20, "bold")
        )
        self.title_label.pack(anchor="w", padx=20, pady=(20, 10))

        self.desc_label = ctk.CTkLabel(
            self,
            text="Сохраняйте и загружайте шаблоны метаданных",
            font=("Arial", 12),
            text_color="gray60"
        )
        self.desc_label.pack(anchor="w", padx=20, pady=(0, 20))

        # Две колонки
        self._create_two_columns()

        # Обновляем список
        self._refresh_list()

    def _create_two_columns(self):
        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Левая колонка — список шаблонов
        left = ctk.CTkFrame(columns, corner_radius=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            left,
            text="📂 Мои шаблоны",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Список
        self.templates_listbox = ctk.CTkScrollableFrame(left)
        self.templates_listbox.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Кнопки
        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="➕ Создать",
            width=80,
            command=self._create_template
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_row,
            text="📂 Импорт",
            width=80,
            command=self._import_template
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_row,
            text="🗑 Удалить",
            width=80,
            fg_color=colors["error"],
            hover_color=colors["error"],
            command=self._delete_template
        ).pack(side="left", padx=2)

        # Правая колонка — редактор
        right = ctk.CTkFrame(columns, corner_radius=12)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            right,
            text="✏️ Редактор шаблона",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self._create_editor_fields(right)

    def _create_editor_fields(self, parent):
        fields = [
            ("Название", "name"),
            ("Название организации", "title"),
            ("Тема", "subject"),
            ("Комментарий", "comment"),
            ("Автор", "artist"),
            ("Авторские права", "copyright"),
            ("Услуги", "services"),
        ]

        self.entries = {}

        for label, key in fields:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)

            ctk.CTkLabel(
                row,
                text=label,
                width=150,
                anchor="w",
                font=("Arial", 12)
            ).pack(side="left")

            if key == "services":
                entry = ClippableTextbox(row, height=80)
            else:
                entry = ClippableEntry(row, height=32)

            entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.entries[key] = entry

        # Кнопки
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(10, 10))

        ctk.CTkButton(
            btn_row,
            text="💾 Сохранить",
            width=120,
            command=self._save_template
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_row,
            text="📤 Экспорт",
            width=120,
            command=self._export_template
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_row,
            text="🧹 Очистить",
            width=120,
            command=self._clear_editor
        ).pack(side="left", padx=2)

    def _refresh_list(self):
        """Обновляет список шаблонов."""
        # Очищаем
        for widget in self.templates_listbox.winfo_children():
            widget.destroy()

        # Загружаем шаблоны
        templates = TemplateManager.list_templates()

        if not templates:
            ctk.CTkLabel(
                self.templates_listbox,
                text="Нет шаблонов",
                font=("Arial", 12),
                text_color="gray50"
            ).pack(pady=20)
            return

        for name in sorted(templates):
            btn = ctk.CTkButton(
                self.templates_listbox,
                text=f"📄 {name}",
                anchor="w",
                fg_color="transparent",
                text_color="white",
                hover_color="gray30",
                command=lambda n=name: self._load_template(n)
            )
            btn.pack(fill="x", pady=2)

    def _load_template(self, name: str):
        """Загружает шаблон в редактор."""
        try:
            data = TemplateManager.load(name)
            self.current_template = name

            # Заполняем поля
            for key, entry in self.entries.items():
                value = data.get(key, "")
                if key == "services":
                    entry.delete("1.0", "end")
                    entry.insert("1.0", value)
                else:
                    entry.delete(0, "end")
                    entry.insert(0, value)

            # Подсвечиваем в списке
            self._refresh_list()

        except TemplateError as e:
            messagebox.showerror("Ошибка", str(e))

    def _save_template(self):
        """Сохраняет шаблон из редактора."""
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Введите название шаблона!")
            return

        data = {
            "name": name,
            "title": self.entries["title"].get(),
            "subject": self.entries["subject"].get(),
            "comment": self.entries["comment"].get(),
            "artist": self.entries["artist"].get(),
            "copyright": self.entries["copyright"].get(),
            "services": self.entries["services"].get("1.0", "end-1c").strip(),
        }

        try:
            TemplateManager.save(name, data)
            self.current_template = name
            self._refresh_list()
            messagebox.showinfo("Успех", f"Шаблон '{name}' сохранён!")
        except TemplateError as e:
            messagebox.showerror("Ошибка", str(e))

    def _delete_template(self):
        """Удаляет текущий шаблон."""
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Выберите шаблон для удаления!")
            return

        if not messagebox.askyesno("Подтверждение", f"Удалить шаблон '{name}'?"):
            return

        try:
            TemplateManager.delete(name)
            self.current_template = None
            self._clear_editor()
            self._refresh_list()
            messagebox.showinfo("Успех", f"Шаблон '{name}' удалён!")
        except TemplateError as e:
            messagebox.showerror("Ошибка", str(e))

    def _create_template(self):
        """Создаёт новый шаблон."""
        self._clear_editor()
        self.entries["name"].focus_set()
        self.current_template = None

    def _export_template(self):
        """Экспортирует шаблон в файл."""
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Выберите шаблон для экспорта!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Экспорт шаблона",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                TemplateManager.export(name, Path(file_path))
                messagebox.showinfo("Успех", f"Шаблон '{name}' экспортирован!")
            except TemplateError as e:
                messagebox.showerror("Ошибка", str(e))

    def _import_template(self):
        """Импортирует шаблон из файла."""
        file_path = filedialog.askopenfilename(
            title="Импорт шаблона",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                name = TemplateManager.import_from_file(Path(file_path))
                self._refresh_list()
                self._load_template(name)
                messagebox.showinfo("Успех", f"Шаблон '{name}' импортирован!")
            except TemplateError as e:
                messagebox.showerror("Ошибка", str(e))

    def _clear_editor(self):
        """Очищает поля редактора."""
        for key, entry in self.entries.items():
            if key == "services":
                entry.delete("1.0", "end")
            else:
                entry.delete(0, "end")
        self.current_template = None