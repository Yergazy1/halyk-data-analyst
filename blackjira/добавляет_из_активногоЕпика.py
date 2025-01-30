import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from dateutil import parser

# Настройки для подключения к Jira
JIRA_URL = "https://jira.adacta-fintech.com"
EMAIL = "halyk_nazguls"
API_TOKEN = "MjnXny82BAqX!e4E"

# Настройки для Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-b68f41c814e4.json", SCOPE)
client = gspread.authorize(CREDS)

# Открытие таблицы
spreadsheet = client.open("from black jira")  # Название Google Sheets
worksheet = spreadsheet.get_worksheet(0)  # Первый лист таблицы

# Очистка таблицы перед записью
worksheet.clear()
worksheet.append_row(["ID Задачи", "Исполнитель", "Создатель", "Статус", "Эпик", "Изменение статусов"])
SPRINT_ID = 3424  # ID спринта Halyk_January_2_2025

# Функция для преобразования даты
def format_date(iso_date):
    dt = parser.parse(iso_date)
    return dt.strftime("%d.%m.%Y %H:%M")

# Функция для получения названия задачи по ID (для эпика)
def get_issue_title(issue_id):
    issue_url = f"{JIRA_URL}/rest/api/2/issue/{issue_id}"
    response = requests.get(issue_url, auth=(EMAIL, API_TOKEN), verify=False)
    if response.status_code == 200:
        issue_data = response.json()
        return issue_data.get('fields', {}).get('summary', 'Без названия')
    else:
        print(f"Ошибка при запросе задачи {issue_id}: {response.status_code}")
        return 'Ошибка при получении названия'

# Получаем задачи из конкретного спринта
start_at = 0
is_last = False

while not is_last:
    url = f"{JIRA_URL}/rest/agile/1.0/sprint/{SPRINT_ID}/issue"
    params = {
        "fields": "key,assignee,creator,status,customfield_10008,issuetype",
        "expand": "changelog",
        "startAt": start_at,
        "maxResults": 50  # Количество задач на страницу
    }

    response = requests.get(url, auth=(EMAIL, API_TOKEN), params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        is_last = data.get("isLast", False)  # Проверяем, последняя ли страница

        if not issues:
            print("Больше задач нет.")
            break

        for issue in issues:
            issue_key = issue["key"]
            fields = issue["fields"]
            assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Не назначен"
            creator = fields["creator"]["displayName"]
            status = fields["status"]["name"]

            # Проверка, является ли задача эпиком
            issue_type = fields.get("issuetype", {}).get("name", "")
            if issue_type == "Epic":
                print(f"Задача {issue_key} - эпик, пропускаем.")
                continue

            # Определение эпика
            epic = fields.get("customfield_10008", "Нет эпика")
            if epic and epic != "Нет эпика":
                epic_title = get_issue_title(epic)
                epic = f"{epic} ({epic_title})"

            # Получение истории изменений статусов
            changelog = issue.get("changelog", {}).get("histories", [])
            status_changes = []
            seen_statuses = set()

            for history in changelog:
                for item in history.get("items", []):
                    if item["field"] == "status":
                        to_status = item["toString"]
                        changed_time = format_date(history["created"])

                        if to_status not in seen_statuses:
                            status_changes.append(f"{to_status} {changed_time}")
                            seen_statuses.add(to_status)

            # Записываем в Google Sheets
            worksheet.append_row([
                issue_key,
                assignee,
                creator,
                status,
                epic,
                "\n".join(status_changes)
            ])

        start_at += len(issues)
        print(f"Загружено задач: {start_at}")

    else:
        print(f"Ошибка при запросе задач: {response.status_code}, {response.text}")
        break

print(f"Все задачи из спринта Halyk_January_2_2025 (ID: {SPRINT_ID}) загружены в Google Sheets.")
