import requests
import json

# Настройки Jira
JIRA_URL = "https://jira.adacta-fintech.com"
EMAIL = "halyk_nazguls"
API_TOKEN = "MjnXny82BAqX!e4E"

# Запрос на получение первых 5 задач
url = f"{JIRA_URL}/rest/api/2/search"
params = {
    "maxResults": 30,  # Получаем только 5 задач
    "fields": "*all",  # Получаем все доступные поля
}

response = requests.get(url, auth=(EMAIL, API_TOKEN), params=params, verify=False)

if response.status_code == 200:
    data = response.json()
    with open("jira_issues.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print("✅ Данные записаны в jira_issues.json. Открой файл, чтобы посмотреть структуру.")
else:
    print(f"❌ Ошибка запроса: {response.status_code} - {response.text}")
