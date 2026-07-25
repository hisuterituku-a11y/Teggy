from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.metadata.metadata_service import MetadataService


def test_supported_formats_are_jpeg_only() -> None:
    assert MetadataService.can_read("photo.jpg") is True
    assert MetadataService.can_read("photo.JPEG") is True
    assert MetadataService.can_write("photo.jpeg") is True
    assert MetadataService.can_read("photo.png") is False
    assert MetadataService.can_write("photo.webp") is False


def test_get_format_info_for_png() -> None:
    info = MetadataService.get_format_info("photo.png")

    assert info == {
        "format": "PNG",
        "extension": ".png",
        "can_read_metadata": False,
        "can_write_metadata": False,
        "needs_conversion": True,
        "is_jpg": False,
    }


def test_read_metadata_returns_empty_dict_for_unsupported_format() -> None:
    assert MetadataService.read_metadata("photo.png") == {}


def test_convert_png_to_jpg(tmp_path) -> None:
    source = tmp_path / "photo.png"
    Image.new("RGBA", (20, 10), (255, 0, 0, 128)).save(source)

    output = MetadataService.convert_to_jpg(str(source), quality=90)

    assert output == str(tmp_path / "photo.jpg")
    output_path = Path(output)
    assert output_path.exists()
    with Image.open(output_path) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"
        assert image.size == (20, 10)


def test_process_file_converts_then_writes_metadata(tmp_path, monkeypatch) -> None:
    source = tmp_path / "photo.png"
    output = tmp_path / "photo.jpg"
    source.write_bytes(b"source")

    calls: list[tuple] = []

    def fake_convert(file_path: str, quality: int = 95) -> str:
        calls.append(("convert", file_path, quality))
        output.write_bytes(b"jpeg")
        return str(output)

    def fake_write(file_path: str, metadata: dict) -> bool:
        calls.append(("write", file_path, metadata))
        return True

    monkeypatch.setattr(MetadataService, "convert_to_jpg", staticmethod(fake_convert))
    monkeypatch.setattr(MetadataService, "write_metadata", staticmethod(fake_write))

    metadata = {"title": "Клиника"}
    result = MetadataService.process_file(str(source), metadata)

    assert result == {
        "success": True,
        "output_path": str(output),
        "message": "Готово",
    }
    assert calls == [
        ("convert", str(source), 95),
        ("write", str(output), metadata),
    ]


def test_process_file_can_delete_original_after_conversion(tmp_path, monkeypatch) -> None:
    source = tmp_path / "photo.png"
    output = tmp_path / "photo.jpg"
    source.write_bytes(b"source")

    def fake_convert(file_path: str, quality: int = 95) -> str:
        output.write_bytes(b"jpeg")
        return str(output)

    monkeypatch.setattr(MetadataService, "convert_to_jpg", staticmethod(fake_convert))
    monkeypatch.setattr(
        MetadataService,
        "write_metadata",
        staticmethod(lambda file_path, metadata: True),
    )

    result = MetadataService.process_file(
        str(source),
        {"title": "Фото"},
        delete_original=True,
    )

    assert result["success"] is True
    assert source.exists() is False


def test_process_file_reports_conversion_failure(tmp_path, monkeypatch) -> None:
    source = tmp_path / "photo.webp"
    source.write_bytes(b"source")
    monkeypatch.setattr(
        MetadataService,
        "convert_to_jpg",
        staticmethod(lambda file_path, quality=95: None),
    )

    assert MetadataService.process_file(str(source), {}) == {
        "success": False,
        "output_path": None,
        "message": "Ошибка конвертации",
    }


def test_process_file_reports_metadata_failure(tmp_path, monkeypatch) -> None:
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"jpeg")
    monkeypatch.setattr(
        MetadataService,
        "write_metadata",
        staticmethod(lambda file_path, metadata: False),
    )

    assert MetadataService.process_file(str(source), {}) == {
        "success": False,
        "output_path": str(source),
        "message": "Ошибка записи метаданных",
    }
