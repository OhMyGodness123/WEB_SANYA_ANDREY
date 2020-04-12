from requests import get, delete, post

print(get('http://127.0.0.1:1414/api/v1/news/5').json())
print(delete('http://localhost:1414/api/v1/news/5'))
print(get('http://127.0.0.1:1414/api/v1/news/5').json())
print(post('http://localhost:1414/api/v1/news', json={'id': '43',
                                                        'color': '141',
                                                        'title': 'привет',
                                                        'text': 'fjasdfjasdjfjasdjfhjdsh',
                                                        'creator': 'OHHHHH',
                                                        'date_of_create': '32121',
                                                        'category': 'Новости'}))
print(get('http://127.0.0.1:1414/api/v1/news/43').json())