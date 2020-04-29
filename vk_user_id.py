import vk


def vk_changed_ssilka(user_id):
    user_id = user_id.split('/')[-1]
    access_token = '362847a543e3b224bc93c5546ae46d7d49184c0089d4827e66bee971260bbc2345cf7c1e5ea86760c5bea'
    v = '5.00'
    session = vk.Session(access_token=access_token)
    api = vk.API(session, v=v)
    if 'vk' not in user_id:
        raise TypeError
    screen_name = user_id
    try:
        id = api.utils.resolveScreenName(screen_name=screen_name)['object_id']
    except TypeError:
        return f'https://vk.com/im?sel={user_id.split("/")[-1]}'
    return f'https://vk.com/im?sel={id}'


def old_ssika(user_ssilka):
    return f'https://vk.com/{user_ssilka.split("=")[-1]}'
