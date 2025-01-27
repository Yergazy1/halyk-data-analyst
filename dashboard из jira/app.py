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
JIRA_URL = "https://dpir.skhalyk.kz/jira/browse/ADACTA-17"
EMAIL = "sultanova.naz"
PAT = "NTUyOTQyMjkzNDQxOiOpsPswxrel0va/xizH1YAhv0Qr"
jira = JIRA(server=JIRA_URL, basic_auth=(EMAIL, PAT))

# Получаем список задач из Jira
board_id = 1009
issues = jira.search_issues(f"board={board_id}", maxResults=1000)

# Преобразуем задачи из Jira в формат для таблицы
tasks = []
for issue in issues:
    task = {
        "task": issue.key,
        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Не назначено",
        "status": issue.fields.status.name
    }
    tasks.append(task)

# Получаем существующие задачи из Google Sheets
existing_task_keys = [worksheet.cell(row, 1).value for row in range(2, worksheet.row_count + 1)]

# Удаляем задачи, которые больше не существуют в Jira
for row_number, task_key in enumerate(existing_task_keys, start=2):  # начинаем с 2, так как первая строка - это заголовки
    if task_key not in [task["task"] for task in tasks]:
        worksheet.delete_row(row_number)
        print(f"Задача {task_key} удалена из таблицы.")

# Обновление или добавление оставшихся задач
for task in tasks:
    if task["task"] in existing_task_keys:
        # Обновление существующих задач
        row_number = existing_task_keys.index(task["task"]) + 2
        existing_assignee = worksheet.cell(row_number, 2).value
        existing_status = worksheet.cell(row_number, 3).value

        if task["assignee"] != existing_assignee:
            worksheet.update_cell(row_number, 2, task["assignee"])
        if task["status"] != existing_status:
            worksheet.update_cell(row_number, 3, task["status"])

        print(f"Задача {task['task']} обновлена.")
    else:
        # Добавление новых задач
        worksheet.append_row([task["task"], task["assignee"], task["status"]])
        print(f"Задача {task['task']} добавлена.")
