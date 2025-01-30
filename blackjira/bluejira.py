import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time  # Импортируем модуль для задержки
from datetime import datetime  # Импортируем datetime для работы с датами

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

# Очистка Google Sheets перед записью
worksheet.clear()
worksheet.append_row(["ID Задачи", "Исполнитель", "Создатель", "Статус", "Эпик", "Изменение статусов"])

# Параметры для запросов
url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/issue"
params = {
    "fields": "key,assignee,creator,status,customfield_10008,issuetype",  # Добавляем поле для типа задачи
    "expand": "changelog",  # Добавляем историю изменений
}

# Инициализация переменных для пагинации
start_at = 0  # Индекс начала
is_last = False  # Флаг последней страницы

# Функция для преобразования даты в нужный формат
def format_date(iso_date):
    # Преобразуем строку даты в объект datetime
    dt = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S.%f+0500")
    # Преобразуем объект datetime в нужный формат
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

# Обработка задач в цикле
while not is_last:
    params["startAt"] = start_at  # Указываем начальный индекс для текущей страницы

    response = requests.get(
        url,
        auth=(EMAIL, API_TOKEN),
        params=params,
        verify=False  # Отключаем проверку SSL
    )

    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        is_last = data.get("isLast", False)  # Флаг последней страницы

        if not issues:
            print("Больше задач нет. Выход из цикла.")
            break

        # Обрабатываем задачи
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
                continue  # Пропускаем эпик

            # Ищем эпик в истории изменений
            changelog = issue.get("changelog", {}).get("histories", [])
            epic = 'Нет эпика'
            epic_link = ''  # Для ссылки на эпик
            for history in changelog:
                for item in history.get("items", []):
                    if item.get("field") == 'Ссылка на эпик':
                        epic = item.get("toString", 'Нет эпика')
                        epic_link = f"{JIRA_URL}/browse/{epic}"  # Формируем ссылку на эпик
                        break

            if epic != 'Нет эпика':
                # Получаем название эпика
                epic_title = get_issue_title(epic)
                epic = f"{epic} ({epic_title})"
                print(f"Эпик: {epic}")
            else:
                print("Нет эпика.")
            
            # Получение изменений статусов
            status_changes = []
            seen_statuses = set()  # Множество для отслеживания уже обработанных статусов
            for history in changelog:
                for item in history.get("items", []):
                    if item["field"] == "status":
                        from_status = item["fromString"]
                        to_status = item["toString"]
                        changed_time = format_date(history["created"])  # Форматируем время

                        # Записываем только, если этот статус ещё не встречался
                        if to_status not in seen_statuses:
                            status_changes.append(f"{to_status} {changed_time}")
                            seen_statuses.add(to_status)

            # Записываем в таблицу
            worksheet.append_row([
                issue_key,
                assignee,
                creator,
                status,
                epic,  # Добавляем эпик
                "\n".join(status_changes)
            ])

        # Увеличиваем индекс для следующей страницы
        start_at += len(issues)
        print(f"Загружено задач: {start_at}")

        # Задержка на 1 секунду перед следующим запросом, чтобы избежать превышения квоты
        time.sleep(60)

    else:
        print(f"Ошибка при запросе задач: {response.status_code}, {response.text}")
        break

print("Задачи из Backlog успешно загружены.")
