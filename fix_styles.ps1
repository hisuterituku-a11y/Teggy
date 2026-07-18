$style = @'
/* Глобальный стиль для всех кнопок */
QPushButton {
    border-radius: 8px;
}

/* Глобальный стиль для всех полей ввода */
QLineEdit, QTextEdit {
    border-radius: 8px;
    padding: 6px 10px;
    background: @colors_bg;
    color: @colors_text;
    border: 1px solid @colors_border;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: @colors_accent;
}

QLineEdit:disabled, QTextEdit:disabled {
    color: @colors_text_secondary;
}

QWidget {
    background: @colors_bg;
    color: @colors_text;
}

.Card {
    background: @colors_card;
    border-radius: @radius_md px;
}

QPushButton[class="PrimaryButton"] {
    background: @colors_accent;
    color: @colors_text;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: bold;
}

QPushButton[class="PrimaryButton"]:hover {
    background: @colors_accent_hover;
}

QPushButton[class="PrimaryButton"]:pressed {
    background: @colors_accent_pressed;
}

QPushButton[class="PrimaryButton"]:disabled {
    background: @colors_border;
    color: @colors_text_secondary;
}

QPushButton[class="SecondaryButton"] {
    background: transparent;
    color: @colors_accent;
    border: 1px solid @colors_accent;
    border-radius: 8px;
    padding: 8px 20px;
}

QPushButton[class="SecondaryButton"]:hover {
    background: @colors_accent;
    color: @colors_text;
}

QPushButton[class="SecondaryButton"]:pressed {
    background: @colors_accent_pressed;
    border-color: @colors_accent_pressed;
}

QPushButton[class="SecondaryButton"]:disabled {
    border-color: @colors_border;
    color: @colors_text_secondary;
}

QPushButton[class="IconButton"] {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px;
}

QPushButton[class="IconButton"]:hover {
    background: @colors_hover;
}

QPushButton[class="IconButton"]:pressed {
    background: @colors_border;
}

.TextField {
    background: @colors_bg;
    color: @colors_text;
    border: 1px solid @colors_border;
    border-radius: 8px;
    padding: 6px 10px;
}

.TextField:focus {
    border-color: @colors_accent;
}

.TextField:disabled {
    color: @colors_text_secondary;
}

.TagEditor {
    background: @colors_bg;
    color: @colors_text;
    border: 1px solid @colors_border;
    border-radius: 8px;
    padding: 6px 10px;
}

.TagEditor:focus {
    border-color: @colors_accent;
}

.FileList {
    background: @colors_bg;
    color: @colors_text;
    border: 1px solid @colors_border;
    border-radius: 8px;
}

.FileList::item {
    padding: @spacing_sm px @spacing_md px;
}

.FileList::item:selected {
    background: @colors_accent;
    color: @colors_text;
}

.FileList::item:hover:!selected {
    background: @colors_hover;
}

QProgressBar {
    background: @colors_surface;
    border: none;
    border-radius: 8px;
    height: 8px;
}

QProgressBar::chunk {
    background: @colors_accent;
    border-radius: 8px;
}

.LogWidget {
    background: @colors_bg;
    color: @colors_text_secondary;
    border: 1px solid @colors_border;
    border-radius: 8px;
    font-family: "Consolas";
    font-size: 11px;
}

.Header {
    background: @colors_card;
    border-bottom: 1px solid @colors_border;
}

.HeaderLogo {
    color: @colors_text;
    font-size: @typography_size_large px;
    font-weight: bold;
}

.HeaderButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px;
}

.HeaderButton:hover {
    background: @colors_hover;
}

.Sidebar {
    background: @colors_card;
    border-right: 1px solid @colors_border;
}

.SidebarButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: @spacing_sm px;
}

.SidebarButton:hover {
    background: @colors_hover;
}

.SidebarButton:pressed {
    background: @colors_accent;
}

.Inspector {
    background: @colors_card;
    border-left: 1px solid @colors_border;
}

.InspectorTitle {
    color: @colors_text;
    font-size: @typography_size_large px;
    font-weight: bold;
}

.InspectorInfo {
    color: @colors_text_secondary;
}

.InspectorPlaceholder {
    color: @colors_text_secondary;
}

.InspectorSubtitle {
    color: @colors_text;
    font-weight: bold;
}

.InspectorMetadata {
    color: @colors_text;
}

.InspectorMuted {
    color: @colors_text_secondary;
    font-style: italic;
}

.BottomLog {
    background: @colors_bg;
    border-top: 1px solid @colors_border;
}
'@

# Применяем ко всем темам
Get-ChildItem -Path assets\themes -Directory | ForEach-Object {
    $filePath = Join-Path $_.FullName "style.qss"
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($filePath, $style, $utf8NoBom)
    Write-Host "✅ Обновлён: $filePath" -ForegroundColor Green
}

Write-Host "`n✅ Все темы обновлены!" -ForegroundColor Green
Write-Host "Запусти: python main.py" -ForegroundColor Yellow