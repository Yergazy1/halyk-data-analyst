import requests
import gspread
from dateutil import parser
from oauth2client.service_account import ServiceAccountCredentials
import os

# Настройки для подключения к Jira
JIRA_URL = "https://dpir.skhalyk.kz/jira"
EMAIL = "sultanova.naz"
API_TOKEN = "Qwerty123456789!!"
BOARD_ID = 37  # ID вашей доски

# Ввод названия спринта вручную
sprint_name = input("Введите название спринта: ")

def get_sprint_by_name(name):
    sprint_url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint"
    start_at = 0
    while True:
        params = {'startAt': start_at, 'maxResults': 50}
        response = requests.get(sprint_url, auth=(EMAIL, API_TOKEN), params=params, verify=False)
        if response.status_code == 200:
            sprints = response.json().get('values', [])
            for sprint in sprints:
                if sprint['name'] == name:
                    return sprint
            if not sprints:
                break
            start_at += len(sprints)
        else:
            print(f"Ошибка при запросе спринтов: {response.status_code}")
            return None
    return None

SPRINT = get_sprint_by_name(sprint_name)
if not SPRINT:
    print(f"Спринт '{sprint_name}' не найден. Завершение работы.")
    exit()

SPRINT_ID = SPRINT["id"]
print(f"ID выбранного спринта: {SPRINT_ID}")

# Настройки для Google Sheets
os.environ['REQUESTS_CA_BUNDLE'] = "GTSRootR4.crt"
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-2a591559bd63.json", SCOPE)
client = gspread.authorize(creds)
spreadsheet = client.open("from jira")
worksheet = spreadsheet.get_worksheet(0)    
worksheet.clear()
headers = ["Исполнитель", "Ключ задачи", "Создатель", "Статус", "Открыто", "В работе", "Тестирование", "Готово", "Перенесем в Спринт 3"]
worksheet.insert_row(headers, index=1)

url = f"{JIRA_URL}/rest/agile/1.0/sprint/{SPRINT_ID}/issue"
params = {"fields": "key,assignee,creator,status,created", "expand": "changelog"}

# Список задач, которые переносятся в Спринт 3
sprint_3_tasks = {
    "ADACTA-319", "ADACTA-473", "ADACTA-35", "ADACTA-381", "ADACTA-229", "ADACTA-568", "ADACTA-535", "ADACTA-465",
    "ADACTA-222", "ADACTA-550", "ADACTA-245", "ADACTA-277", "ADACTA-531", "ADACTA-536", "ADACTA-428", "ADACTA-529",
    "ADACTA-475", "ADACTA-32", "ADACTA-551", "ADACTA-606", "ADACTA-51", "ADACTA-501", "ADACTA-539", "ADACTA-141",
    "ADACTA-549", "ADACTA-116", "ADACTA-215", "ADACTA-364", "ADACTA-50", "ADACTA-242", "ADACTA-315", "ADACTA-294",
    "ADACTA-607", "ADACTA-590", "ADACTA-424", "ADACTA-217", "ADACTA-416", "ADACTA-279"
}

def format_date(iso_date):
    dt = parser.parse(iso_date)
    return dt.strftime("%d.%m")

start_at = 0
rows_to_insert = []
while True:
    params["startAt"] = start_at
    response = requests.get(url, auth=(EMAIL, API_TOKEN), params=params, verify=False)
    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        if not issues:
            break
        for issue in issues:
            issue_key = issue["key"]
            fields = issue["fields"]
            assignee = fields["assignee"]["displayName"] if fields["assignee"] else "Не назначен"
            creator = fields["creator"]["displayName"]
            status = fields["status"]["name"]
            created_date = format_date(fields["created"])
            changelog = issue.get("changelog", {}).get("histories", [])
            
            status_mapping = {"Open": "Open", "In Progress": "В работе", "In Testing": "Posttest", "Done": "Готово"}
            mapped_status = {v: k for k, v in status_mapping.items()}
            status_changes = {key: "" for key in status_mapping.keys()}
            
            for history in changelog:
                for item in history.get("items", []):
                    if item["field"] == "status":
                        to_status = item["toString"]
                        changed_time = format_date(history["created"])
                        if to_status in mapped_status:
                            status_changes[mapped_status[to_status]] = changed_time
            
            if not status_changes["Open"]:
                status_changes["Open"] = created_date
            
            transfer_status = "Да" if issue_key in sprint_3_tasks else "Нет"
            
            rows_to_insert.append([
                assignee, issue_key, creator, status,
                status_changes["Open"], status_changes["In Progress"],
                status_changes["In Testing"], status_changes["Done"],
                transfer_status
            ])
        
        start_at += len(issues)
        if rows_to_insert:
            worksheet.append_rows(rows_to_insert, value_input_option="RAW")
            rows_to_insert.clear()
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
        break

print("Задачи успешно загружены.")
