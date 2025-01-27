import gspread
from oauth2client.service_account import ServiceAccountCredentials
from jira import JIRA

# Настройки для подключения к Jira
JIRA_URL = "https://dpir.skhalyk.kz/jira"
EMAIL = "sultanova.naz"
API_TOKEN = "Qwerty123456789!"

try:
    # Подключение к Jira
    jira = JIRA(server=JIRA_URL, basic_auth=(EMAIL, API_TOKEN), options={'server': JIRA_URL, 'verify': False})

    # ID доски
    BOARD_ID = 35

    # Настройки для Google Sheets
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    CREDS = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-b68f41c814e4.json", SCOPE)
    client = gspread.authorize(CREDS)

    # Открытие таблицы
    spreadsheet = client.open("from jira")  # Название таблицы
    worksheet = spreadsheet.get_worksheet(0)  # Первый лист таблицы

    def get_board_issues(board_id):
        """
        Получает задачи с указанной доски.
        """
        try:
            # Получаем ключи проектов, привязанных к доске
            board_projects = jira.board_projects(board_id)
            project_keys = [proj.key for proj in board_projects["values"]]

            # Формируем JQL для фильтрации задач
            jql_query = f"project IN ({', '.join(project_keys)})"
            issues = jira.search_issues(jql_query, maxResults=100)
            return issues
        except Exception as e:
            print(f"Ошибка при запросе задач доски: {e}")
            return []

    def get_issue_changelog(issue_key):
        """
        Получает историю изменений задачи.
        """
        try:
            issue = jira.issue(issue_key, expand="changelog")
            changelog = issue.changelog.histories
            return changelog
        except Exception as e:
            print(f"Ошибка при запросе истории задачи {issue_key}: {e}")
            return []

    def main():
        # Получаем задачи с доски
        issues = get_board_issues(BOARD_ID)

        print(f"Найдено {len(issues)} задач на доске {BOARD_ID}.")
        rows = [["ID", "Исполнитель", "Статус", "Создатель", "Изменено"]]  # Заголовки таблицы

        for issue in issues:
            issue_key = issue.key
            fields = issue.fields
            assignee = fields.assignee.displayName if fields.assignee else "Не назначен"
            status = fields.status.name
            creator = fields.creator.displayName

            print(f"\nЗадача: {issue_key}")
            print(f"Исполнитель: {assignee}, Статус: {status}, Создатель: {creator}")

            # Получаем историю изменений задачи
            changelog = get_issue_changelog(issue_key)
            status_changes = []

            for change in changelog:
                for item in change.items:
                    if item.field == "status":
                        from_status = item.fromString
                        to_status = item.toString
                        changed_at = change.created
                        status_changes.append(f"{changed_at}: {from_status} → {to_status}")

            # Сохраняем информацию в список строк
            rows.append([issue_key, assignee, status, creator, "\n".join(status_changes)])

        # Обновляем данные в Google Sheets
        worksheet.update("A1", rows)  # Записываем данные в таблицу

    if __name__ == "__main__":
        main()

except Exception as e:
    print(f"Ошибка подключения к Jira: {e}")
