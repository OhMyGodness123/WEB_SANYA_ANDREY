from requests import get, delete, post

print(get('http://127.0.0.1:1414/api/v1/news/5').json())  # Получение 5 темы
print(delete('http://localhost:1414/api/v1/news/10'))  # Удаление 10 темы
print(get('http://127.0.0.1:1414/api/v1/news').json())  # Получение всех тем
print(post('http://localhost:1414/api/v1/news', json={'id': '43',
                                                      'color': 'FF0F0F',
                                                      'title': 'Api theme',
                                                      'text': '',
                                                      'creator': 1,
                                                      'date_of_create': '2020-04-12',
                                                      'category': 'Новости'}))
# Добавление новости
print(get('http://127.0.0.1:1414/api/v1/news/43').json())  # Получение добавленной темы
