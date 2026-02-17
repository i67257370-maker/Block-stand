[app]

# Название игры в телефоне
title = Block Blast Neon

# Имя пакета (без пробелов)
package.name = blockblastneon

# Твоё имя или ник
package.domain = org.neondev

# Папка с кодом (текущая)
source.dir = .

# Расширения файлов, которые нужно включить в APK
source.include_exts = py,png,jpg,kv,atlas,json

# Версия твоей игры
version = 1.0.0

# БИБЛИОТЕКИ (Очень важно!)
# Мы добавляем python3 и kivy. Pillow нужен для работы с изображениями, если они есть.
requirements = python3,kivy==2.3.0,hostpython3,pillow

# Ориентация экрана (только вертикально)
orientation = portrait

# Полноэкранный режим (скрывает часы и уведомления сверху)
fullscreen = 1

# Иконка приложения (если нет своей, закомментируй)
# icon.filename = %(source.dir)s/icon.png

# (android) Настройки для Android
android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b

# Архитектуры процессоров (arm64-v8a для новых телефонов)
android.archs = arm64-v8a, armeabi-v7a

# (python-for-android) Настройки сборки
p4a.branch = master

[buildozer]
# Уровень логирования (2 — показывать ошибки и процесс)
log_level = 2

# Предупреждать перед выполнением команд под root
warn_on_root = 1