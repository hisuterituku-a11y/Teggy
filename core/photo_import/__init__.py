from core.photo_import.models import (
    PhotoInfo, ImportTask, ImportProgress,
    SourceType, ImportStatus,
)
# ИСПРАВЛЕНО: раньше исключения (PhotoImportError, ParserError,
# DownloadError, NetworkError, CancelledError, SourceNotSupportedError)
# импортировались из core.photo_import.models. После того как из
# models.py убрали дублирующие определения этих классов (они там были
# самостоятельными, но одноимёнными классами, отличными от классов в
# exceptions.py — см. models.py), этот импорт стал бы падать с
# ImportError. Теперь исключения импортируются из их единственного
# настоящего места — core.photo_import.exceptions.
from core.photo_import.exceptions import (
    PhotoImportError, ParserError, DownloadError,
    NetworkError, CancelledError, SourceNotSupportedError,
)

# ИСПРАВЛЕНО: PhotoImportService раньше импортировался дважды — один раз
# абсолютным путём (core.photo_import.service), один раз относительным
# (.service). Оба импорта указывают на один и тот же класс, второй просто
# бесполезно перезаписывал то же самое имя. Оставлен один вариант.
from core.photo_import.service import PhotoImportService

from core.photo_import.providers import YandexParser, GoogleParser, TwoGISParser
