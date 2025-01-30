import requests

# Настройки для подключения к Jira
JIRA_URL = "https://jira.adacta-fintech.com"
EMAIL = "halyk_nazguls"
API_TOKEN = "MjnXny82BAqX!e4E"
BOARD_ID = 1009  # ID вашей доски

# Функция для получения всех спринтов с учётом пагинации
def get_all_sprints():
    sprint_url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint"
    sprints = []
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
            sprints.extend(sprint_data.get('values', []))
            is_last = sprint_data.get('isLast', False)
            start_at += len(sprint_data.get('values', []))  # Переходим к следующей странице
        else:
            print(f"Ошибка при запросе спринтов: {response.status_code}")
            break
    
    return sprints

# Получаем все спринты
all_sprints = get_all_sprints()

# Выводим информацию о всех спринтах
if all_sprints:
    print("Спринты:")
    for sprint in all_sprints:
        print(f"ID: {sprint['id']}, Название: {sprint['name']}, Статус: {sprint['state']}")
else:
    print("Спринты не найдены.")
