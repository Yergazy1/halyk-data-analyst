import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройки для подключения к Jira
JIRA_URL = "https://dpir.skhalyk.kz/jira"
EMAIL = "sultanova.naz"
API_TOKEN = "Qwerty123456789!"
BOARD_ID = 35  # ID вашей доски

# Настройки для Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-b68f41c814e4.json", SCOPE)
client = gspread.authorize(CREDS)

# Открытие таблицы
spreadsheet = client.open("from jira")  # Название вашей таблицы
worksheet = spreadsheet.get_worksheet(0)  # Первый лист таблицы

# Получение задач с доски
url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/issue"
params = {
    "maxResults": 100,  # Количество задач за раз (поменяйте при необходимости)
    "fields": "key,assignee,creator,status",  # Поля для получения
    "expand": "changelog"  # Добавляем историю изменений
}

response = requests.get(
    url,
    auth=(EMAIL, API_TOKEN),
    verify=False  # Отключаем проверку SSL
)

if response.status_code == 200:
    issues = response.json().get("issues", [])

    # Очистка Google Sheets перед записью
    worksheet.clear()
    worksheet.append_row(["ID Задачи", "Исполнитель", "Создатель", "Статус", "Изменение статусов"])

    # Обработка задач
    for issue in issues:
        issue_key = issue["key"]
        fields = issue["fields"]
        assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Не назначен"
        creator = fields["creator"]["displayName"]
        status = fields["status"]["name"]

        # Получение времени изменений статусов из changelog
        changelog = issue.get("changelog", {}).get("histories", [])
        status_changes = []
        for history in changelog:
            for item in history.get("items", []):
                if item["field"] == "status":
                    from_status = item["fromString"]
                    to_status = item["toString"]
                    changed_time = history["created"]
                    status_changes.append(f"{from_status} -> {to_status} ({changed_time})")

        # Запись данных в Google Sheets
        worksheet.append_row([
            issue_key,
            assignee,
            creator,
            status,
            "\n".join(status_changes)  # Все изменения статуса в одной ячейке
        ])

    print("Данные успешно записаны в Google Sheets.")
else:
    print(f"Ошибка при запросе задач: {response.status_code}, {response.text}")
