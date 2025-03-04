import requests

JIRA_URL = "https://dpir.skhalyk.kz/jira"
EMAIL = "sultanova.naz"
API_TOKEN = "Qwerty123456789!!"
BOARD_ID = 37

sprint_2_name = "Спринт 2"
sprint_3_name = "Спринт 3"

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
                    return sprint['id']
            if not sprints:
                break
            start_at += len(sprints)
        else:
            print(f"Ошибка при запросе спринтов: {response.status_code}")
            return None
    return None

sprint_2_id = get_sprint_by_name(sprint_2_name)
sprint_3_id = get_sprint_by_name(sprint_3_name)

if not sprint_2_id or not sprint_3_id:
    print("Один из спринтов не найден. Завершение работы.")
    exit()

def get_tasks_from_sprint(sprint_id):
    url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
    start_at = 0
    tasks = set()
    while True:
        params = {"startAt": start_at, "maxResults": 50}
        response = requests.get(url, auth=(EMAIL, API_TOKEN), params=params, verify=False)
        if response.status_code == 200:
            issues = response.json().get("issues", [])
            if not issues:
                break
            for issue in issues:
                tasks.add(issue["key"])
            start_at += len(issues)
        else:
            print(f"Ошибка при запросе задач: {response.status_code}")
            break
    return tasks

sprint_2_tasks = get_tasks_from_sprint(sprint_2_id)
sprint_3_tasks = get_tasks_from_sprint(sprint_3_id)

common_tasks = sprint_2_tasks & sprint_3_tasks

print("Задачи, которые есть в двух спринтах:")
for task in common_tasks:
    print(task)