import requests
import gspread
from dateutil import parser
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time  
import certifi
import os


# pip install requests gspread oauth2client python-dateutil

# Настройки для подключения к Jira
JIRA_URL = "https://dpir.skhalyk.kz/jira"
EMAIL = "sultanova.naz"
API_TOKEN = "Qwerty123456789!!"
BOARD_ID = 37  # ID вашей доски

# Функция получения активного спринта
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
if not SPRINT:
    print("Активный спринт не найден. Завершение работы.")
    exit()

SPRINT_ID = SPRINT["id"]
print(f"ID активного спринта: {SPRINT_ID}")

# Настройки для Google Sheets
os.environ['REQUESTS_CA_BUNDLE'] = "GTSRootR4.crt"

# Дальше ваш код
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-2a591559bd63.json", SCOPE)

# Авторизация в Google Sheets
client = gspread.authorize(creds)



# Открываем таблицу
spreadsheet = client.open("from jira")
worksheet = spreadsheet.get_worksheet(0)    

# Очистка Google Sheets перед записью
worksheet.clear()
headers = ["Эпик", "Исполнитель", "Ключ задачи", "Создатель", "Статус", "Открыто", "В работе", "Решено", "Тестирование", "Готово"]
worksheet.insert_row(headers, index=1)

# URL запроса задач
url = f"{JIRA_URL}/rest/agile/1.0/sprint/{SPRINT_ID}/issue"
params = {
    "fields": "key,assignee,creator,status,customfield_10008,issuetype",
    "expand": "changelog",
}

# Функция для преобразования даты
def format_date(iso_date):
    dt = parser.parse(iso_date)
    return dt.strftime("%d.%m")

# Функция для получения названия эпика
def get_issue_title(issue_id):
    issue_url = f"{JIRA_URL}/rest/api/2/issue/{issue_id}"
    response = requests.get(issue_url, auth=(EMAIL, API_TOKEN), verify=False)
    if response.status_code == 200:
        issue_data = response.json()
        return issue_data.get('fields', {}).get('summary', 'Без названия')
    return 'Ошибка при получении названия'

# Начальные параметры пагинации
start_at = 0
is_last = False
rows_to_insert = []  # Список для массовой вставки данных

while not is_last:
    params["startAt"] = start_at
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

            # Проверка, является ли задача эпиком
            issue_type = fields.get("issuetype", {}).get("name", "")
            if issue_type == "Epic":
                print(f"Задача {issue_key} является эпиком, пропускаем.")
                continue  

            # Поиск эпика в истории изменений
            changelog = issue.get("changelog", {}).get("histories", [])
            epic = 'Нет эпика'
            for history in changelog:
                for item in history.get("items", []):
                    if item.get("field") == 'Ссылка на эпик':
                        epic = item.get("toString", 'Нет эпика')
                        break

            # Получаем название эпика, если он есть
            if epic != 'Нет эпика':
                epic_title = get_issue_title(epic)
                epic = f"{epic} ({epic_title})"

            # Словарь соответствия статусов
            status_mapping = {
                "Open": "Открыто",
                "In Progress": "В работе",
                "Resolved": "Решено",
                "In Testing": "Тестирование",
                "Done": "Готово"
            }

            mapped_status = {v: k for k, v in status_mapping.items()}
            status_changes = {key: "" for key in status_mapping.keys()}

            for history in changelog:
                for item in history.get("items", []):
                    if item["field"] == "status":
                        to_status = item["toString"]
                        changed_time = format_date(history["created"])
                        if to_status in mapped_status:
                            status_changes[mapped_status[to_status]] = changed_time

            # Добавляем строку в список для массовой вставки
            rows_to_insert.append([
                epic,
                assignee,
                issue_key,
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

        # Отправляем данные в Google Sheets одним запросом после обработки всех задач
        if rows_to_insert:
            start_row = len(worksheet.get_all_values()) + 1  # Берём первую свободную строку
            cell_range = f"A{start_row}"
            
            worksheet.update(cell_range, rows_to_insert, value_input_option="RAW")
            rows_to_insert.clear()

    else:
        print(f"Ошибка при запросе задач: {response.status_code}, {response.text}")
        break

print("Задачи из Backlog успешно загружены.")

# Запуск Google Apps Script для сортировки
GAS_URL = "https://script.google.com/macros/s/AKfycbyuurBDAzJ7RN7oWJUjR3Lh-dLm8H_xEUQuys-KImzXfXDK9SXkdAsBvSVyleapde6q/exec"
def run_sorting_script():
    try:
        response = requests.get(GAS_URL, verify=False)
        if response.status_code == 200:
            print("Сортировка завершена!")
        else:
            print("Ошибка при запуске GAS:", response.text)
    except Exception as e:
        print("Ошибка запроса:", e)

def main():
    print("Выполняем Python-скрипт...")
    print("Запускаем Google Apps Script для сортировки...")
    run_sorting_script()

if __name__ == "__main__":
    main()
