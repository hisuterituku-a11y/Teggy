from typing import Dict, List


class ThemeValidationError(Exception):
    pass


class ThemeValidator:
    """Проверяет структуру темы."""

    REQUIRED_COLORS = ["bg", "card", "text", "text_secondary", "accent", "border"]
    REQUIRED_SPACING = ["xs", "sm", "md", "lg", "xl"]
    REQUIRED_RADIUS = ["sm", "md", "lg"]

    @classmethod
    def validate(cls, data: Dict) -> None:
        errors: List[str] = []

        # Проверяем colors
        colors = data.get("colors", {})
        for key in cls.REQUIRED_COLORS:
            if key not in colors:
                errors.append(f"Missing key: colors.{key}")

        # Проверяем spacing
        spacing = data.get("spacing", {})
        for key in cls.REQUIRED_SPACING:
            if key not in spacing:
                errors.append(f"Missing key: spacing.{key}")

        # Проверяем radius
        radius = data.get("radius", {})
        for key in cls.REQUIRED_RADIUS:
            if key not in radius:
                errors.append(f"Missing key: radius.{key}")

        if errors:
            raise ThemeValidationError("\n".join(errors))