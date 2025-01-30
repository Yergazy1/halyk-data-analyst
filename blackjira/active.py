import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time  # Импортируем модуль для задержки
from dateutil import parser  # Импортируем для парсинга даты

# Настройки для подключения к Jira
JIRA_URL = "https://jira.adacta-fintech.com"
EMAIL = "halyk_nazguls"
API_TOKEN = "MjnXny82BAqX!e4E"
BOARD_ID = 1009  # ID вашей доски

# Настройки для Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-b68f41c814e4.json", SCOPE)
client = gspread.authorize(CREDS)

# Открытие таблицы
spreadsheet = client.open("from black jira")  # Название вашей таблицы
worksheet = spreadsheet.get_worksheet(0)  # Первый лист таблицы

# Очистка Google Sheets перед записью
worksheet.clear()
worksheet.append_row(["ID Задачи", "Исполнитель", "Создатель", "Статус", "Эпик", "Изменение статусов"])

# Параметры для запросов
url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/issue"
params = {
    "fields": "key,assignee,creator,status,customfield_10008,issuetype",
    "expand": "changelog",
}

start_at = 0  # Индекс начала
is_last = False  # Флаг последней страницы

# Функция для преобразования даты в нужный формат
def format_date(iso_date):
    dt = parser.parse(iso_date)  # Автоматически парсит дату
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

# Функция для получения активного спринта
def get_active_sprint():
    sprint_url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint"
    start_at = 0
    is_last = False

    while not is_last:
        # Параметры запроса для пагинации
        params = {
            'startAt': start_at,
            'maxResults': 50  # Максимальное количество спринтов на одну страницу
        }

        response = requests.get(sprint_url, auth=(EMAIL, API_TOKEN), params=params, verify=False)

        if response.status_code == 200:
            sprint_data = response.json()
            sprints = sprint_data.get('values', [])
            is_last = sprint_data.get('isLast', False)
            start_at += len(sprints)  # Переходим к следующей странице

            for sprint in sprints:
                if sprint['state'] in ['active', 'started', 'open']:  # Проверка на статус активного спринта
                    return sprint  # Возвращаем активный спринт
        else:
            print(f"Ошибка при запросе спринтов: {response.status_code}")
            break

    return None  # Возвращаем None, если не нашли активный спринт

# Получаем активный спринт
active_sprint = get_active_sprint()

# Выводим информацию о найденном активном спринте
if active_sprint:
    print(f"Активный спринт найден: {active_sprint['name']} (ID: {active_sprint['id']})")
else:
    print("Активный спринт не найден.")
    exit()  # Завершаем выполнение, если активного спринта нет

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

            # Проверка, принадлежит ли задача активному спринту
            sprint_id = fields.get("customfield_10004")  # ID спринта задачи
            if sprint_id != active_sprint['id']:  # Если задача не из активного спринта
                continue

            # Ищем эпик в истории изменений
            # Получаем эпик из поля customfield_10008
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
            seen_statuses = set()

            for history in changelog:
                for item in history.get("items", []):
                    if item["field"] == "status":
                        from_status = item["fromString"]
                        to_status = item["toString"]
                        changed_time = format_date(history["created"])  # Форматируем время

                        if to_status not in seen_statuses:
                            status_changes.append(f"{to_status} {changed_time}")
                            seen_statuses.add(to_status)

            # Записываем в таблицу
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

print("Задачи из активного спринта успешно загружены.")
