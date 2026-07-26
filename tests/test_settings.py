from __future__ import annotations

import json

from core.settings import Settings


def test_defaults_when_settings_file_does_not_exist(tmp_path, monkeypatch) -> None:
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(Settings, "SETTINGS_FILE", settings_file)

    assert Settings.get_last_folder() == ""
    assert Settings.get_theme() == "default"
    assert Settings.get_delete_original() is False
    assert Settings.get_last_template() == ""
    assert Settings.get_window_geometry() == {
        "x": 100,
        "y": 100,
        "width": 1280,
        "height": 820,
    }


def test_settings_round_trip(tmp_path, monkeypatch) -> None:
    settings_file = tmp_path / "nested" / "settings.json"
    monkeypatch.setattr(Settings, "SETTINGS_FILE", settings_file)

    Settings.save_last_folder("X:/Photos")
    Settings.save_theme("light")
    Settings.save_delete_original(True)
    Settings.save_last_template("Clinic")
    Settings.save_window_geometry(10, 20, 1400, 900)

    assert Settings.get_last_folder() == "X:/Photos"
    assert Settings.get_theme() == "light"
    assert Settings.get_delete_original() is True
    assert Settings.get_last_template() == "Clinic"
    assert Settings.get_window_geometry() == {
        "x": 10,
        "y": 20,
        "width": 1400,
        "height": 900,
    }


def test_invalid_json_falls_back_to_defaults(tmp_path, monkeypatch) -> None:
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{broken json", encoding="utf-8")
    monkeypatch.setattr(Settings, "SETTINGS_FILE", settings_file)

    assert Settings.get_theme() == "default"
    assert Settings.get_dashboard_stats() == {
        "processed_files": 0,
        "templates_created": 0,
        "last_run": "",
    }


def test_dashboard_counters_never_decrease_below_zero(tmp_path, monkeypatch) -> None:
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(Settings, "SETTINGS_FILE", settings_file)

    Settings.update_dashboard_stats(
        processed_files=-50,
        templates_created=-10,
        last_run="2026-07-25T12:00",
    )
    Settings.increment_processed_files(3)
    Settings.increment_processed_files(-100)
    Settings.increment_templates_created(2)
    Settings.increment_templates_created(-100)

    assert Settings.get_dashboard_stats() == {
        "processed_files": 3,
        "templates_created": 2,
        "last_run": "2026-07-25T12:00",
    }


def test_settings_file_contains_valid_utf8_json(tmp_path, monkeypatch) -> None:
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(Settings, "SETTINGS_FILE", settings_file)

    Settings.save_last_template("Шаблон клиники")

    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert data["last_template"] == "Шаблон клиники"
