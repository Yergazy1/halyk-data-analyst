from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Авторизация в Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-b68f41c814e4.json", scope)
client = gspread.authorize(creds)

# Открытие таблицы
spreadsheet = client.open("from jira")  # Название вашей таблицы
worksheet = spreadsheet.get_worksheet(0)  # Открываем первый лист

# Пример задач
tasks = [
    {
        "task": "PROJ-101",
        "created": "2025-01-15T12:00:00",
        "resolved": "2025-01-18T15:00:00",
        "creator": "Иван Иванов",
        "assignee": "Мария Петрова",
        "status": "В процессе",
        "epic": "EPIC-1"
    },
    {
        "task": "PROJ-102",
        "created": "2025-01-10T09:00:00",
        "resolved": "2025-01-17T11:00:00",
        "creator": "Мария Петрова",
        "assignee": "Не назначено",
        "status": "Завершено",
        "epic": "EPIC-2"
    },
    {
        "task": "PROJ-103",
        "created": "2025-01-13T14:30:00",
        "resolved": None,
        "creator": "Иван Иванов",
        "assignee": "Не назначено",
        "status": "Ожидание",
        "epic": None
    }
]

# Добавление задач в таблицу
for task in tasks:
    worksheet.append_row([
        task["task"], 
        task["created"], 
        task["resolved"] if task["resolved"] else "Не завершено", 
        task["creator"], 
        task["assignee"], 
        task["status"], 
        task["epic"] if task["epic"] else "Не связано"
    ])

print("Задачи успешно добавлены в таблицу.")
