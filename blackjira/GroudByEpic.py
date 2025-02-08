import requests
import json
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
BOARD_ID = 1009  # ID вашей доски

def get_active_sprint():
    sprint_url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint"
    start_at = 0
    is_last = False

    while not is_last:
        params = {
            'startAt': start_at,
            'maxResults': 50
        }

        response = requests.get(sprint_url, auth=(EMAIL, API_TOKEN), params=params, verify=False)

        if response.status_code == 200:
            sprint_data = response.json()
            
            sprints = sprint_data.get('values', [])
            is_last = sprint_data.get('isLast', False)
            start_at += len(sprints)

            for sprint in sprints:
                if sprint['state'] in ['active', 'started', 'open']:
                    return sprint
        else:
            print(f"Ошибка при запросе спринтов: {response.status_code}")
            break

    return None

SPRINT = get_active_sprint()
SPRINT_ID = SPRINT["id"]
print(SPRINT_ID)

def format_date(iso_date):
    dt = parser.parse(iso_date)
    return dt.strftime("%d.%m")

start_at = 0
is_last = False

while not is_last:
    url = f"{JIRA_URL}/rest/agile/1.0/sprint/{SPRINT_ID}/issue"
    params = {
        "fields": "key,summary,assignee,creator,status,customfield_10710,issuetype",
        "expand": "changelog",
        "startAt": start_at,
        "maxResults": 50
    }

    response = requests.get(url, auth=(EMAIL, API_TOKEN), params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        is_last = data.get("isLast", False)

        if not issues:
            print("Больше задач нет.")
            break

        for issue in issues:
            issue_key = issue["key"]
            fields = issue["fields"]
            assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Не назначен"
            creator = fields["creator"]["displayName"]
            status = fields["status"]["name"]
            summary = fields["summary"]

            issue_type = fields.get("issuetype", {}).get("name", "")
            if issue_type == "Epic":
                print(f"Задача {issue_key} - эпик, пропускаем.")
                continue

            epic = fields.get("customfield_10710") or "Нет эпика"

            changelog = issue.get("changelog", {}).get("histories", [])
            status_changes = {
                "Open": "",
                "In Progress": "",
                "Resolved": "",
                "In Testing": "",
                "Done": ""
            }

            for history in changelog:
                for item in history.get("items", []):
                    if item["field"] == "status":
                        to_status = item["toString"]
                        changed_time = format_date(history["created"])

                        if to_status in status_changes:
                            status_changes[to_status] = changed_time

            worksheet.append_row([
                epic,
                assignee,
                f"{issue_key} - {summary}",
                creator,
                status,
                status_changes["Open"],
                status_changes["In Progress"],
                status_changes["Resolved"],
                status_changes["In Testing"],
                status_changes["Done"]
            ])

        start_at += len(issues)
        print(f"Загружено задач: {start_at}")

    else:
        print(f"Ошибка при запросе задач: {response.status_code}, {response.text}")
        break

print(f"Все задачи из спринта Halyk_January_2_2025 (ID: {SPRINT_ID}) загружены в Google Sheets.")



# URL Google Apps Script (замени на свой)
GAS_URL = "https://script.google.com/macros/s/AKfycbwFcplJCZxEbUaMne98XVU17HYN7w_Wa3FGbibexTgsrNIDutMry8y_5HBqTZSUB-CK3w/exec"

def run_sorting_script():
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            print("Сортировка завершена!")
        else:
            print("Ошибка при запуске GAS:", response.text)
    except Exception as e:
        print("Ошибка запроса:", e)

# Основной код Python
def main():
    print("Выполняем Python-скрипт...")
    # Здесь твой код

    print("Запускаем Google Apps Script для сортировки...")
    run_sorting_script()

if __name__ == "__main__":
    main()
