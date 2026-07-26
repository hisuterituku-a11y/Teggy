from pathlib import Path


class ThemeData:

    def __init__(self, qss: str):
        self.qss = qss



class ThemeManager:

    def __init__(self, themes_path=None):

        self.themes_path = Path(
            themes_path
        ) if themes_path else Path(__file__).parent



    def load(self, theme_name: str):

        print(
            "LOAD THEME:",
            theme_name
        )


        # Новая система Teggy
        if theme_name == "default":

            qss_file = (
                Path(__file__).resolve()
                .parents[2]
                / "assets"
                / "themes"
                / "default"
                / "style.qss"
            )


            if qss_file.exists():

                print(
                    "LOADING:",
                    qss_file
                )

                return ThemeData(
                    qss_file.read_text(
                        encoding="utf-8"
                    )
                )


            print(
                "Default theme not found:",
                qss_file
            )

            return ThemeData("")


        # Старые темы пока оставляем
        theme_folder = (
            self.themes_path
            / theme_name
        )


        if not theme_folder.exists():

            return ThemeData("")


        qss_parts = []


        for name in [
            "style.qss",
            "dashboard.qss",
            "inspector.qss",
        ]:

            file = theme_folder / name

            if file.exists():

                qss_parts.append(
                    file.read_text(
                        encoding="utf-8"
                    )
                )


        return ThemeData(
            "\n\n".join(qss_parts)
        )