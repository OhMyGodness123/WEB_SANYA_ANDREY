import vk_api


def vk_changed_ssilka(user_id):
    login, password = '77713753075', 'YURA2000'
    vk_session = vk_api.VkApi(
        login, password,  captcha_handler=captcha_handler
    )
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return
    vk = vk_session.get_api()
    try:
        user_id = user_id.split('/')[-1]
        response = vk.users.get(user_ids=user_id)[0]['id']
        return f'https://vk.com/im?sel={response}'
    except Exception:
        return 'error'


def captcha_handler(captcha):
    """ При возникновении капчи вызывается эта функция и ей передается объект
        капчи. Через метод get_url можно получить ссылку на изображение.
        Через метод try_again можно попытаться отправить запрос с кодом капчи
    """

    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key)


def old_ssika(user_ssilka):
    return f'https://vk.com/{user_ssilka.split("=")[-1]}'
