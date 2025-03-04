import json

# Твой JSON-объект
data = { ... }  # Вставь сюда свой JSON

# Достаем версию окружения
environment_version = data.get("fields", {}).get("customfield_11400", "Не указано")

print(f"Окружение (версия): {environment_version}")
