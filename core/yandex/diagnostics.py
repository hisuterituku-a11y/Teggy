from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable
import json
import platform
import sys
import traceback


def format_exception_report(
    *,
    stage: str,
    exc: BaseException,
    url: str | None = None,
) -> str:
    """Формирует читаемый отчёт об ошибке для журнала."""
    tb = traceback.TracebackException.from_exception(exc)
    frames = list(tb.stack)

    source_file = ""
    source_line = ""

    if frames:
        last = frames[-1]
        source_file = last.filename
        source_line = str(last.lineno)

    lines = [
        "[ERROR] ================================================",
        f"[ERROR] Этап: {stage}",
        f"[ERROR] Тип: {type(exc).__name__}",
        f"[ERROR] Сообщение: {exc}",
    ]

    if url:
        lines.append(f"[ERROR] URL: {url}")

    if source_file:
        lines.append(f"[ERROR] Файл: {source_file}")

    if source_line:
        lines.append(f"[ERROR] Строка: {source_line}")

    lines.extend(
        [
            "[ERROR] Полный traceback:",
            "".join(tb.format()).rstrip(),
            "[ERROR] ================================================",
        ]
    )

    return "\n".join(lines)


def save_diagnostic_report(
    *,
    save_dir: Path | str,
    stage: str,
    exc: BaseException,
    url: str | None = None,
    log_lines: Iterable[str] = (),
    extra: dict | None = None,
) -> Path:
    """Сохраняет текстовую диагностику в отдельную папку."""
    save_dir = Path(save_dir)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_stage = "".join(
        char if char.isalnum() or char in ("-", "_") else "_"
        for char in stage.strip().lower()
    ).strip("_") or "error"

    diagnostic_dir = (
        save_dir
        / "diagnostics"
        / f"{timestamp}_{safe_stage}"
    )
    diagnostic_dir.mkdir(parents=True, exist_ok=True)

    exception_report = format_exception_report(
        stage=stage,
        exc=exc,
        url=url,
    )

    (diagnostic_dir / "error.txt").write_text(
        "\n".join(
            [
                f"Этап: {stage}",
                f"Тип ошибки: {type(exc).__name__}",
                f"Сообщение: {exc}",
                f"URL: {url or 'не указан'}",
            ]
        ),
        encoding="utf-8",
    )

    (diagnostic_dir / "traceback.txt").write_text(
        "".join(
            traceback.TracebackException
            .from_exception(exc)
            .format()
        ),
        encoding="utf-8",
    )

    (diagnostic_dir / "log.txt").write_text(
        "\n".join(str(line) for line in log_lines),
        encoding="utf-8",
    )

    system_info = {
        "python": sys.version,
        "platform": platform.platform(),
        "stage": stage,
        "url": url,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
    }

    if extra:
        system_info.update(extra)

    (diagnostic_dir / "system.json").write_text(
        json.dumps(
            system_info,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (diagnostic_dir / "REPORT.txt").write_text(
        exception_report,
        encoding="utf-8",
    )

    return diagnostic_dir
