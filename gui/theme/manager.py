from pathlib import Path


class ThemeData:
    def __init__(self, qss: str):
        self.qss = qss


class ThemeManager:

    def __init__(self, themes_path):
        self.themes_path = Path(themes_path)


    def load(self, theme_name: str):

        theme_folder = self.themes_path / theme_name

        if not theme_folder.exists():
            return ThemeData("")


        qss_parts = []


        # основной стиль
        style = theme_folder / "style.qss"

        if style.exists():
            print("LOADING STYLE:", style)
            
            qss_parts.append(
                style.read_text(
                    encoding="utf-8"
                )
            )


        # дополнительные стили
        dashboard = theme_folder / "dashboard.qss"

        if dashboard.exists():
            qss_parts.append(
                dashboard.read_text(
                    encoding="utf-8"
                )
            )


        inspector = theme_folder / "inspector.qss"

        if inspector.exists():
            qss_parts.append(
                inspector.read_text(
                    encoding="utf-8"
                )
            )


        return ThemeData(
            "\n\n".join(qss_parts)
        )