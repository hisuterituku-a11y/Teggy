from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin

import requests


LogCallback = Callable[[str], None]
CancelCallback = Callable[[], bool]


class DashDownloadError(RuntimeError):
    """Ошибка загрузки или сборки DASH-видео."""


@dataclass(frozen=True)
class DashTrack:
    kind: str
    representation_id: str
    bandwidth: int
    base_urls: tuple[str, ...]
    initialization: str
    segments: tuple[str, ...]


class DashDownloader:
    """Скачивает DASH-сегменты через requests и объединяет локально."""

    MPD_NS = "urn:mpeg:dash:schema:mpd:2011"

    def __init__(
        self,
        ffmpeg_path: str,
        timeout: int = 60,
        retries: int = 3,
    ) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.timeout = timeout
        self.retries = retries

    @staticmethod
    def _log(text: str, on_log: LogCallback | None) -> None:
        if on_log:
            on_log(text)

    @staticmethod
    def _duration_seconds(value: str | None) -> float | None:
        if not value:
            return None
        match = re.fullmatch(
            r"P(?:(?P<days>[\d.]+)D)?T"
            r"(?:(?P<hours>[\d.]+)H)?"
            r"(?:(?P<minutes>[\d.]+)M)?"
            r"(?:(?P<seconds>[\d.]+)S)?",
            value,
        )
        if not match:
            return None
        return (
            float(match.group("days") or 0) * 86400
            + float(match.group("hours") or 0) * 3600
            + float(match.group("minutes") or 0) * 60
            + float(match.group("seconds") or 0)
        )

    @staticmethod
    def _replace_template(
        template: str,
        *,
        representation_id: str,
        bandwidth: int,
        number: int | None = None,
        time_value: int | None = None,
    ) -> str:
        value = template
        value = value.replace("$RepresentationID$", representation_id)
        value = value.replace("$Bandwidth$", str(bandwidth))

        def replace_number(match: re.Match[str]) -> str:
            if number is None:
                raise DashDownloadError("В шаблоне нужен Number, но номер не задан")
            width = match.group(1)
            return f"{number:0{int(width)}d}" if width else str(number)

        def replace_time(match: re.Match[str]) -> str:
            if time_value is None:
                raise DashDownloadError("В шаблоне нужен Time, но время не задано")
            width = match.group(1)
            return f"{time_value:0{int(width)}d}" if width else str(time_value)

        value = re.sub(r"\$Number(?:%0(\d+)d)?\$", replace_number, value)
        value = re.sub(r"\$Time(?:%0(\d+)d)?\$", replace_time, value)
        return value.replace("$$", "$")

    def _timeline_values(
        self,
        timeline: ET.Element,
        *,
        period_seconds: float | None,
        timescale: int,
    ) -> list[int]:
        namespace = {"mpd": self.MPD_NS}
        values: list[int] = []
        current = 0
        items = timeline.findall("mpd:S", namespace)

        for index, item in enumerate(items):
            duration = int(item.get("d", "0"))
            if duration <= 0:
                raise DashDownloadError("В SegmentTimeline найден сегмент без duration")

            if item.get("t") is not None:
                current = int(item.get("t", "0"))

            repeat = int(item.get("r", "0"))
            if repeat < 0:
                next_start: int | None = None
                if index + 1 < len(items) and items[index + 1].get("t") is not None:
                    next_start = int(items[index + 1].get("t", "0"))
                elif period_seconds is not None:
                    next_start = int(period_seconds * timescale)

                if next_start is None:
                    raise DashDownloadError(
                        "Не удалось вычислить число повторов SegmentTimeline"
                    )
                repeat = max(0, ((next_start - current) // duration) - 1)

            for _ in range(repeat + 1):
                values.append(current)
                current += duration

        return values

    @staticmethod
    def _child_texts(element: ET.Element, tag: str) -> list[str]:
        values: list[str] = []
        for child in element.findall(tag):
            if child.text and child.text.strip():
                values.append(child.text.strip())
        return values

    def _resolve_base_urls(
        self,
        manifest_url: str,
        root: ET.Element,
        period: ET.Element,
        adaptation: ET.Element,
        representation: ET.Element,
    ) -> tuple[str, ...]:
        ns = f"{{{self.MPD_NS}}}BaseURL"
        levels = [root, period, adaptation, representation]
        urls = [manifest_url]

        for level in levels:
            additions = self._child_texts(level, ns)
            if not additions:
                continue
            urls = [urljoin(base, addition) for base in urls for addition in additions]

        unique: list[str] = []
        seen: set[str] = set()
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return tuple(unique)

    def _build_track(
        self,
        *,
        kind: str,
        manifest_url: str,
        root: ET.Element,
        period: ET.Element,
        adaptation: ET.Element,
        representation: ET.Element,
        period_seconds: float | None,
    ) -> DashTrack:
        ns = {"mpd": self.MPD_NS}
        template = representation.find("mpd:SegmentTemplate", ns)
        if template is None:
            template = adaptation.find("mpd:SegmentTemplate", ns)
        if template is None:
            raise DashDownloadError(f"Для дорожки {kind} не найден SegmentTemplate")

        initialization = template.get("initialization")
        media = template.get("media")
        if not initialization or not media:
            raise DashDownloadError(
                f"Для дорожки {kind} отсутствует initialization или media"
            )

        representation_id = representation.get("id", "")
        bandwidth = int(representation.get("bandwidth", "0") or 0)
        initialization = self._replace_template(
            initialization,
            representation_id=representation_id,
            bandwidth=bandwidth,
        )

        segment_names: list[str] = []
        timeline = template.find("mpd:SegmentTimeline", ns)
        if timeline is not None:
            timescale = int(template.get("timescale", "1") or 1)
            for time_value in self._timeline_values(
                timeline,
                period_seconds=period_seconds,
                timescale=timescale,
            ):
                segment_names.append(
                    self._replace_template(
                        media,
                        representation_id=representation_id,
                        bandwidth=bandwidth,
                        time_value=time_value,
                    )
                )
        else:
            duration = int(template.get("duration", "0") or 0)
            timescale = int(template.get("timescale", "1") or 1)
            if duration <= 0 or period_seconds is None:
                raise DashDownloadError(
                    f"Для дорожки {kind} нельзя вычислить число сегментов"
                )
            count = max(1, int((period_seconds * timescale + duration - 1) // duration))
            start_number = int(template.get("startNumber", "1") or 1)
            for number in range(start_number, start_number + count):
                segment_names.append(
                    self._replace_template(
                        media,
                        representation_id=representation_id,
                        bandwidth=bandwidth,
                        number=number,
                    )
                )

        return DashTrack(
            kind=kind,
            representation_id=representation_id,
            bandwidth=bandwidth,
            base_urls=self._resolve_base_urls(
                manifest_url,
                root,
                period,
                adaptation,
                representation,
            ),
            initialization=initialization,
            segments=tuple(segment_names),
        )

    def _parse_manifest(
        self,
        manifest_url: str,
        content: bytes,
    ) -> tuple[DashTrack, DashTrack | None]:
        root = ET.fromstring(content)
        ns = {"mpd": self.MPD_NS}
        period = root.find("mpd:Period", ns)
        if period is None:
            raise DashDownloadError("В MPD не найден Period")

        period_seconds = self._duration_seconds(period.get("duration"))
        if period_seconds is None:
            period_seconds = self._duration_seconds(root.get("mediaPresentationDuration"))

        candidates: dict[str, list[tuple[ET.Element, ET.Element]]] = {
            "video": [],
            "audio": [],
        }
        for adaptation in period.findall("mpd:AdaptationSet", ns):
            content_type = adaptation.get("contentType", "").lower()
            mime_type = adaptation.get("mimeType", "").lower()
            kind = ""
            if content_type in candidates:
                kind = content_type
            elif mime_type.startswith("video/"):
                kind = "video"
            elif mime_type.startswith("audio/"):
                kind = "audio"
            if not kind:
                continue

            for representation in adaptation.findall("mpd:Representation", ns):
                candidates[kind].append((adaptation, representation))

        if not candidates["video"]:
            raise DashDownloadError("В MPD не найдена видеодорожка")

        def score(item: tuple[ET.Element, ET.Element]) -> tuple[int, int]:
            representation = item[1]
            height = int(representation.get("height", "0") or 0)
            bandwidth = int(representation.get("bandwidth", "0") or 0)
            return height, bandwidth

        video_adaptation, video_representation = max(candidates["video"], key=score)
        video_track = self._build_track(
            kind="video",
            manifest_url=manifest_url,
            root=root,
            period=period,
            adaptation=video_adaptation,
            representation=video_representation,
            period_seconds=period_seconds,
        )

        audio_track: DashTrack | None = None
        if candidates["audio"]:
            audio_adaptation, audio_representation = max(
                candidates["audio"],
                key=lambda item: int(item[1].get("bandwidth", "0") or 0),
            )
            audio_track = self._build_track(
                kind="audio",
                manifest_url=manifest_url,
                root=root,
                period=period,
                adaptation=audio_adaptation,
                representation=audio_representation,
                period_seconds=period_seconds,
            )

        return video_track, audio_track

    def _request_bytes(
        self,
        session: requests.Session,
        url: str,
        *,
        headers: dict[str, str],
        cancel: CancelCallback | None,
    ) -> bytes:
        last_error: Exception | None = None
        for _ in range(self.retries):
            if cancel and cancel():
                raise DashDownloadError("Скачивание отменено")
            try:
                response = session.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except requests.RequestException as error:
                last_error = error
        raise DashDownloadError(f"Не удалось скачать {url}: {last_error}")

    def _download_track(
        self,
        session: requests.Session,
        track: DashTrack,
        destination: Path,
        *,
        headers: dict[str, str],
        on_log: LogCallback | None,
        cancel: CancelCallback | None,
    ) -> None:
        errors: list[str] = []
        total = len(track.segments) + 1

        for server_index, base_url in enumerate(track.base_urls, start=1):
            if cancel and cancel():
                raise DashDownloadError("Скачивание отменено")
            destination.unlink(missing_ok=True)
            try:
                with destination.open("wb") as output:
                    init_url = urljoin(base_url, track.initialization)
                    output.write(
                        self._request_bytes(
                            session,
                            init_url,
                            headers=headers,
                            cancel=cancel,
                        )
                    )
                    self._log(
                        f"{track.kind}: сегмент 1/{total}",
                        on_log,
                    )

                    for index, segment in enumerate(track.segments, start=2):
                        segment_url = urljoin(base_url, segment)
                        output.write(
                            self._request_bytes(
                                session,
                                segment_url,
                                headers=headers,
                                cancel=cancel,
                            )
                        )
                        if index == total or index % 5 == 0:
                            self._log(
                                f"{track.kind}: сегмент {index}/{total}",
                                on_log,
                            )

                if destination.stat().st_size < 1024:
                    raise DashDownloadError("Собранная дорожка слишком мала")
                return
            except Exception as error:
                destination.unlink(missing_ok=True)
                errors.append(f"сервер {server_index}: {error}")
                self._log(
                    f"{track.kind}: сервер {server_index} не подошёл, пробуем следующий",
                    on_log,
                )

        raise DashDownloadError("; ".join(errors))

    def _mux(
        self,
        video_path: Path,
        audio_path: Path | None,
        destination: Path,
    ) -> None:
        temp_output = destination.with_name(
            f"{destination.stem}.part{destination.suffix}"
        )
        temp_output.unlink(missing_ok=True)

        command = [
            self.ffmpeg_path,
            "-y",
            "-nostdin",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
        ]
        if audio_path is not None:
            command.extend(["-i", str(audio_path)])
        command.extend(["-c", "copy", "-movflags", "+faststart", str(temp_output)])

        flags = (
            subprocess.CREATE_NO_WINDOW
            if hasattr(subprocess, "CREATE_NO_WINDOW")
            else 0
        )
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
            timeout=180,
            check=False,
        )
        if result.returncode != 0:
            temp_output.unlink(missing_ok=True)
            raise DashDownloadError(
                f"ffmpeg не собрал локальные дорожки: {result.stderr[-2500:]}"
            )
        if not temp_output.exists() or temp_output.stat().st_size < 1024:
            temp_output.unlink(missing_ok=True)
            raise DashDownloadError("ffmpeg создал пустой итоговый файл")

        destination.unlink(missing_ok=True)
        temp_output.replace(destination)

    def download(
        self,
        manifest_url: str,
        destination: Path,
        *,
        headers: dict[str, str] | None = None,
        on_log: LogCallback | None = None,
        cancel: CancelCallback | None = None,
    ) -> None:
        request_headers = {
            "Referer": "https://yandex.ru/maps/",
            "Origin": "https://yandex.ru",
            "User-Agent": "Mozilla/5.0",
            **(headers or {}),
        }
        destination.parent.mkdir(parents=True, exist_ok=True)

        with requests.Session() as session:
            manifest = self._request_bytes(
                session,
                manifest_url,
                headers=request_headers,
                cancel=cancel,
            )
            video_track, audio_track = self._parse_manifest(manifest_url, manifest)
            self._log(
                "DASH: выбраны дорожки "
                f"video={video_track.representation_id}, "
                f"audio={audio_track.representation_id if audio_track else 'нет'}",
                on_log,
            )

            work_dir = Path(tempfile.mkdtemp(prefix="teggy-dash-"))
            try:
                video_path = work_dir / "video_track.mp4"
                audio_path = work_dir / "audio_track.mp4" if audio_track else None
                self._download_track(
                    session,
                    video_track,
                    video_path,
                    headers=request_headers,
                    on_log=on_log,
                    cancel=cancel,
                )
                if audio_track is not None and audio_path is not None:
                    self._download_track(
                        session,
                        audio_track,
                        audio_path,
                        headers=request_headers,
                        on_log=on_log,
                        cancel=cancel,
                    )
                self._mux(video_path, audio_path, destination)
            finally:
                shutil.rmtree(work_dir, ignore_errors=True)
