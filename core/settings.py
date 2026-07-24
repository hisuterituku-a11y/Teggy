import json
from pathlib import Path


class Settings:
    """Управление настройками приложения."""

    SETTINGS_FILE = Path.home() / ".teggy" / "settings.json"

    @classmethod
    def _read(cls) -> dict:
        if not cls.SETTINGS_FILE.exists():
            return {}
        try:
            with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}

    @classmethod
    def _write(cls, data: dict) -> None:
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except OSError:
            pass

    @classmethod
    def get_last_folder(cls) -> str:
        return cls._read().get("last_folder", "")

    @classmethod
    def save_last_folder(cls, folder_path: str):
        data = cls._read()
        data["last_folder"] = folder_path
        cls._write(data)

    @classmethod
    def get_theme(cls) -> str:
        return cls._read().get("theme", "dark")

    @classmethod
    def save_theme(cls, theme_name: str):
        data = cls._read()
        data["theme"] = theme_name
        cls._write(data)

    @classmethod
    def get_window_geometry(cls) -> dict:
        data = cls._read()
        return {
            "x": data.get("window_x", 100),
            "y": data.get("window_y", 100),
            "width": data.get("window_width", 1280),
            "height": data.get("window_height", 820),
        }

    @classmethod
    def save_window_geometry(cls, x: int, y: int, width: int, height: int):
        data = cls._read()
        data.update(
            {
                "window_x": x,
                "window_y": y,
                "window_width": width,
                "window_height": height,
            }
        )
        cls._write(data)

    @classmethod
    def get_delete_original(cls) -> bool:
        return bool(cls._read().get("delete_original", False))

    @classmethod
    def save_delete_original(cls, value: bool):
        data = cls._read()
        data["delete_original"] = value
        cls._write(data)

    @classmethod
    def get_last_template(cls) -> str:
        return cls._read().get("last_template", "")

    @classmethod
    def save_last_template(cls, template_name: str):
        data = cls._read()
        data["last_template"] = template_name
        cls._write(data)

    @classmethod
    def get_dashboard_stats(cls) -> dict:
        data = cls._read()
        return {
            "processed_files": int(data.get("processed_files", 0) or 0),
            "templates_created": int(data.get("templates_created", 0) or 0),
            "last_run": data.get("last_run", ""),
        }

    @classmethod
    def update_dashboard_stats(
        cls,
        *,
        processed_files: int | None = None,
        templates_created: int | None = None,
        last_run: str | None = None,
    ) -> None:
        data = cls._read()
        if processed_files is not None:
            data["processed_files"] = max(0, int(processed_files))
        if templates_created is not None:
            data["templates_created"] = max(0, int(templates_created))
        if last_run is not None:
            data["last_run"] = last_run
        cls._write(data)

    @classmethod
    def increment_processed_files(cls, amount: int) -> None:
        stats = cls.get_dashboard_stats()
        cls.update_dashboard_stats(processed_files=stats["processed_files"] + max(0, int(amount)))

    @classmethod
    def increment_templates_created(cls, amount: int = 1) -> None:
        stats = cls.get_dashboard_stats()
        cls.update_dashboard_stats(templates_created=stats["templates_created"] + max(0, int(amount)))
