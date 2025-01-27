import time
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import requests
from datetime import datetime, timedelta, timezone

# Текущее время в UTC с использованием timezone-aware объекта
now = datetime.now(timezone.utc)

# Авторизация в Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("jiro-448410-b68f41c814e4.json", scope)
client = gspread.authorize(creds)

# Открытие таблицы
spreadsheet = client.open("fromGitlab")  # Название вашей таблицы
worksheet = spreadsheet.get_worksheet(0)  # Открываем первый лист

# Твой персональный токен доступа
token = 'glpat-pLP6vAh8sHsV1fMyCDys'

# ID проекта, для этого заменим на имя проекта в виде 'namespace%2Frepository'
project_id = 'halyk2%2Fproj'

# ID Merge Request, например, 1 для MR с URL 'https://gitlab.com/halyk2/proj/-/merge_requests/1'
mr_id = 1

# Формируем URL для получения комментариев Merge Request
url = f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests/{mr_id}/notes"

# Заголовки с токеном
headers = {
    "PRIVATE-TOKEN": token
}

# Функция для получения комментариев за последние 30 минут
# Функция для получения комментариев за последние 30 минут
def get_recent_comments():
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        comments = response.json()
        recent_comments = []
        
        # Текущее время в UTC
        now = datetime.now(timezone.utc)
        
        # Определяем время в прошлом для фильтрации (30 минут назад)
        time_limit = now - timedelta(minutes=30)
        
        for comment in comments:
            # Преобразуем дату комментария
            created_at = datetime.strptime(comment['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
            
            # Если комментарий был создан за последние 30 минут, добавляем его в список
            if created_at > time_limit:
                recent_comments.append(comment)
            else:
                # Как только нашли комментарий старше 30 минут, выходим из цикла
                break
        
        return recent_comments
    else:
        print(f"Ошибка: {response.status_code}")
        return []


# Основной цикл для периодического опроса
while True:
    recent_comments = get_recent_comments()
    
    if recent_comments:
        for comment in recent_comments:
            # Извлекаем данные комментария
            body = comment['body']
            created_at = comment['created_at']
            author = comment['author']['name']

            # Преобразуем дату в более читабельный формат
            created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d-%m-%Y %H:%M:%S")

            # Проверяем, содержит ли комментарий ненужные строки
            if "requested review from" in body or "assigned to" in body:
                print(f"Пропущен комментарий: {body}")
                continue

            # Добавляем данные в таблицу
            worksheet.append_row([body, created_at, author])
            print(f"Добавлен комментарий: {body}")

    # Ожидаем 30 секунд перед следующим запросом
    time.sleep(30)
