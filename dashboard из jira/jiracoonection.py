import requests
from jira import JIRA

# Настройки для подключения к Jira
JIRA_URL = "https://dpir.skhalyk.kz/jira"
EMAIL = "sultanova.naz"
API_TOKEN = "Qwerty123456789!"

try:
    # Подключение к Jira
    jira = JIRA(server=JIRA_URL, basic_auth=(EMAIL, API_TOKEN), options={'server': JIRA_URL, 'verify': False})

    # ID доски
    board_id = 35

    # REST API для получения всех задач доски
    url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/issue"

    # Выполняем GET-запрос с токеном
    response = requests.get(
        url,
        auth=(EMAIL, API_TOKEN),
        verify=False  # Отключаем проверку SSL-сертификатов
    )

    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        
        print(f"Найдено {len(issues)} задач на доске с ID {board_id}.")
        for issue in issues:
            issue_key = issue["key"]
            fields = issue["fields"]
            assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Не назначен"
            status = fields["status"]["name"]
            creator = fields["creator"]["displayName"]
            print(f"ID: {issue_key}, Исполнитель: {assignee}, Статус: {status}, Создатель: {creator}")
    else:
        print(f"Ошибка при запросе задач доски: {response.status_code}, {response.text}")

except Exception as e:
    print("Ошибка при выполнении запроса:")
    print(e)
