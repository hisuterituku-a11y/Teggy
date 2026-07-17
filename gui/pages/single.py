"""
Страница обработки одного фото.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from threading import Thread
from pathlib import Path

from gui.widgets import ClippableEntry, ClippableTextbox


class SinglePhotoPage(ctk.CTkFrame):
    """Страница обработки одного фото."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.is_running = False
        self.current_file = None

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self,
            text="🖼 Одно фото",
            font=("Arial", 20, "bold")
        )
        self.title_label.pack(anchor="w", padx=20, pady=(20, 10))

        self.desc_label = ctk.CTkLabel(
            self,
            text="Выберите одно фото для обработки",
            font=("Arial", 12),
            text_color="gray60"
        )
        self.desc_label.pack(anchor="w", padx=20, pady=(0, 20))

        # Выбор файла
        self._create_file_section()

        # Две колонки
        self._create_two_columns()

        # Кнопка запуска
        self._create_start_button()

        # Прогресс
        self._create_progress()

    def _create_file_section(self):
        frame = ctk.CTkFrame(self, corner_radius=12)
        frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            frame,
            text="📁 Выберите файл",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(0, 10))

        self.file_entry = ClippableEntry(
            row,
            placeholder_text="Выберите фото...",
            height=40
        )
        self.file_entry.pack(side="left", fill="x", expand=True)

        self.browse_btn = ctk.CTkButton(
            row,
            text="📂 Выбрать",
            width=100,
            height=40,
            command=self._browse_file
        )
        self.browse_btn.pack(side="right", padx=(10, 0))

        # Инфо о файле
        self.file_info = ctk.CTkLabel(
            frame,
            text="Файл не выбран",
            font=("Arial", 11),
            text_color="gray50"
        )
        self.file_info.pack(anchor="w", padx=15, pady=(0, 10))

    def _create_two_columns(self):
        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Левая колонка — метаданные
        left = ctk.CTkFrame(columns, corner_radius=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            left,
            text="📝 Метаданные",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self._create_metadata_fields(left)

        # Правая колонка — теги
        right = ctk.CTkFrame(columns, corner_radius=12)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            right,
            text="🏷️ Услуги / Теги",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self._create_tags_fields(right)

    def _create_metadata_fields(self, parent):
        fields = [
            ("Название", "title"),
            ("Тема", "subject"),
            ("Комментарий", "comment"),
            ("Автор", "artist"),
            ("Авторские права", "copyright"),
        ]

        self.metadata_entries = {}

        for label, key in fields:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)

            ctk.CTkLabel(
                row,
                text=label,
                width=120,
                anchor="w",
                font=("Arial", 12)
            ).pack(side="left")

            entry = ClippableEntry(row, height=32)
            entry.pack(side="left", fill="x", expand=True)
            self.metadata_entries[key] = entry

    def _create_tags_fields(self, parent):
        ctk.CTkLabel(
            parent,
            text="Услуги (по одной на строке)",
            font=("Arial", 12)
        ).pack(anchor="w", padx=15, pady=(0, 5))

        self.services_text = ClippableTextbox(parent, height=80)
        self.services_text.pack(fill="both", expand=True, padx=15, pady=(0, 5))

        self.generate_btn = ctk.CTkButton(
            parent,
            text="✨ Сделать теги",
            height=32,
            command=self._generate_tags
        )
        self.generate_btn.pack(padx=15, pady=5)

        ctk.CTkLabel(
            parent,
            text="Теги",
            font=("Arial", 12)
        ).pack(anchor="w", padx=15, pady=(5, 5))

        self.tags_text = ClippableTextbox(parent, height=80)
        self.tags_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def _create_start_button(self):
        self.start_btn = ctk.CTkButton(
            self,
            text="🚀 ОБРАБОТАТЬ ФОТО",
            height=50,
            font=("Arial", 16, "bold"),
            command=self._start_processing
        )
        self.start_btn.pack(fill="x", padx=20, pady=(0, 10))

    def _create_progress(self):
        frame = ctk.CTkFrame(self, corner_radius=12)
        frame.pack(fill="x", padx=20, pady=(0, 15))

        self.progress = ctk.CTkProgressBar(frame, height=12)
        self.progress.pack(fill="x", padx=15, pady=(10, 5))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            frame,
            text="✅ Готов к работе",
            font=("Arial", 12)
        )
        self.status_label.pack(anchor="w", padx=15, pady=(0, 10))

    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите фото",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.current_file = Path(file_path)
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, str(self.current_file))

            size = self.current_file.stat().st_size
            size_mb = size / (1024 * 1024)
            self.file_info.configure(
                text=f"📄 {self.current_file.name} ({size_mb:.1f} МБ)"
            )

    def _generate_tags(self):
        services = self.services_text.get("1.0", "end-1c").strip()
        if not services:
            messagebox.showwarning("Внимание", "Сначала введите услуги!")
            return

        from core.tag_generator import TagGenerator
        tags = TagGenerator.parse_tags_input(services)

        self.tags_text.delete("1.0", "end")
        self.tags_text.insert("1.0", "\n".join(tags))

    def _start_processing(self):
        if self.is_running:
            return

        file_path = self.file_entry.get().strip()
        if not file_path or not Path(file_path).exists():
            messagebox.showerror("Ошибка", "Выберите существующий файл!")
            return

        tags_text = self.tags_text.get("1.0", "end-1c").strip()
        if not tags_text:
            messagebox.showerror("Ошибка", "Введите услуги или теги!")
            return

        metadata = {
            "title": self.metadata_entries["title"].get(),
            "subject": self.metadata_entries["subject"].get(),
            "comment": self.metadata_entries["comment"].get(),
            "artist": self.metadata_entries["artist"].get(),
            "copyright": self.metadata_entries["copyright"].get(),
            "rating": 5,
        }

        from core.tag_generator import TagGenerator
        tags = TagGenerator.parse_tags_input(tags_text)

        if not tags:
            messagebox.showerror("Ошибка", "Не удалось распознать теги!")
            return

        self.is_running = True
        self.start_btn.configure(state="disabled", text="⏳ ОБРАБОТКА...")
        self.progress.set(0)
        self.status_label.configure(text="🔄 Обработка...")

        thread = Thread(
            target=self._run_processing,
            args=(file_path, metadata, tags)
        )
        thread.daemon = True
        thread.start()

    def _run_processing(self, file_path: str, metadata: dict, tags: list):
        try:
            from core.worker import ProcessingWorker

            worker = ProcessingWorker()
            worker.set_metadata(**metadata)
            worker.set_tags(tags)

            result = worker.process_single(file_path)

            if result["success"]:
                self.status_label.configure(text=f"✅ Готово! {Path(result['file']).name}")
                self.progress.set(1.0)
                messagebox.showinfo("Готово", f"✅ Фото обработано!\n📁 {result['file']}")
            else:
                self.status_label.configure(text=f"❌ Ошибка: {result['error']}")
                messagebox.showerror("Ошибка", result['error'])

        except Exception as e:
            self.status_label.configure(text=f"❌ Ошибка: {e}")
            messagebox.showerror("Ошибка", str(e))

        finally:
            self.is_running = False
            self.start_btn.configure(state="normal", text="🚀 ОБРАБОТАТЬ ФОТО")