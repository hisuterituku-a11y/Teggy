from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings


@dataclass(frozen=True)
class AppStatistics:
    downloaded: int = 0
    tagged: int = 0
    converted: int = 0
    failed: int = 0


class StatisticsStore:
    """Persistent cumulative counters for Teggy activity."""

    _GROUP = "statistics"
    _KEYS = ("downloaded", "tagged", "converted", "failed")

    def __init__(self) -> None:
        self._settings = QSettings("Teggy", "Teggy")

    def load(self) -> AppStatistics:
        self._settings.beginGroup(self._GROUP)
        try:
            values = {
                key: max(0, int(self._settings.value(key, 0)))
                for key in self._KEYS
            }
        finally:
            self._settings.endGroup()
        return AppStatistics(**values)

    def increment(
        self,
        *,
        downloaded: int = 0,
        tagged: int = 0,
        converted: int = 0,
        failed: int = 0,
    ) -> AppStatistics:
        additions = {
            "downloaded": downloaded,
            "tagged": tagged,
            "converted": converted,
            "failed": failed,
        }

        current = self.load()
        current_values = {
            "downloaded": current.downloaded,
            "tagged": current.tagged,
            "converted": current.converted,
            "failed": current.failed,
        }

        self._settings.beginGroup(self._GROUP)
        try:
            for key, addition in additions.items():
                value = current_values[key] + max(0, int(addition))
                self._settings.setValue(key, value)
                current_values[key] = value
            self._settings.sync()
        finally:
            self._settings.endGroup()

        return AppStatistics(**current_values)
