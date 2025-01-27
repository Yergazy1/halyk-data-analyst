from oauth2client.service_account import ServiceAccountCredentials
import gspread
import requests
from datetime import datetime

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

# Отправляем GET запрос
response = requests.get(url, headers=headers)

if response.status_code == 200:
    comments = response.json()
    
    # Добавляем заголовки в таблицу (если их еще нет)
    if worksheet.row_count == 0:
        worksheet.append_row(["Комментарий", "Дата комментария", "Автор"])
    
    for comment in comments:
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
else:
    print(f"Ошибка: {response.status_code}")
