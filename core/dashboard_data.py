# ============================================================
# Teggy Dashboard Data
#
# Источник данных для Dashboard.
#
# Сейчас:
# - демо-данные
#
# Позже:
# - история обработки
# - реальные проекты
# - статистика файлов
# ============================================================



def get_dashboard_stats():

    return {
        "total": 2847,
        "photos": 1245,
        "stories": 892,
        "reviews": 456,
        "processed": 127,
        "saved_time": "12 ч 45 мин",
    }



def get_current_task():

    return {
        "name": "Кофейня «Вкусно»",
        "current": 67,
        "total": 120,
        "progress": 56,
        "status": "🟢 В процессе",
    }



def get_recent_files():

    return [
        (
            "coffee_shop_01.jpg",
            "Фото • 2.4 MB • 12:45"
        ),

        (
            "story_2024_01.mp4",
            "Сторис • 15.8 MB • 12:43"
        ),

        (
            "review_155_01.jpg",
            "Отзыв • 1.1 MB • 12:40"
        ),
    ]