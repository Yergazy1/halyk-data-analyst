from jira import JIRA
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройки для подключения к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-b68f41c814e4.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("from jira")  # Название вашей таблицы
worksheet = spreadsheet.get_worksheet(0)  # Открываем первый лист

# Настройки для подключения к Jira
JIRA_URL = "https://jira.adacta-fintech.com"
EMAIL = "halyk_nazguls"
PAT = "ODUzNTE1NzAxOTA3OjjEXBNWpXvL6qJMkJV6CcV1OihF"
jira = JIRA(server=JIRA_URL, basic_auth=(EMAIL, PAT))

# Получаем список задач из Jira
board_id = 1009
issues = jira.search_issues(f"board={board_id}", maxResults=1000)

# Преобразуем задачи из Jira в формат для таблицы
tasks = []
for issue in issues:
    # Получаем данные задачи
    task = {
        "task": issue.key,
        "created": issue.fields.created,
        "creator": issue.fields.creator.displayName if issue.fields.creator else "Неизвестно",
        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Не назначено",
        "status": issue.fields.status.name,
        "epic": issue.fields 
    }
    tasks.append(task)

# Преобразуем задачи для записи в Google Sheets
existing_task_keys = [worksheet.cell(row, 1).value for row in range(2, worksheet.row_count + 1)]

# Удаляем задачи, которые больше не существуют в Jira
for row_number, task_key in enumerate(existing_task_keys, start=2):
    if task_key not in [task["task"] for task in tasks]:
        worksheet.delete_row(row_number)
        print(f"Задача {task_key} удалена из таблицы.")

# Обновление или добавление задач в таблицу
for task in tasks:
    if task["task"] in existing_task_keys:
        # Обновление существующих задач
        row_number = existing_task_keys.index(task["task"]) + 2
        worksheet.update(f"A{row_number}:G{row_number}", [[
            task["task"],
            task["created"],
            task["resolved"],
            task["creator"],
            task["assignee"],
            task["status"],
            task["epic"]
        ]])
        print(f"Задача {task['task']} обновлена.")
    else:
        # Добавление новых задач
        worksheet.append_row([
            task["task"],
            task["created"],
            task["resolved"],
            task["creator"],
            task["assignee"],
            task["status"],
            task["epic"]
        ])
        print(f"Задача {task['task']} добавлена.")

print("Обновление таблицы завершено.")
