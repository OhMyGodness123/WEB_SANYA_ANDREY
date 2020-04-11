import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
from data import complaint_book, db_session
import json

TOKEN = '8e1b170213715b93663836f626f00140f9c238f03471e83e9139198d5ff62a544f272813440a141530207'
keyboard = {
    "one_time": True,
    "buttons": [[{
        "action": {
            "type": "text",
            "payload": "{\"button\": \"1\"}",
            "label": "!Пожаловаться"
        },
        "color": "negative"
    },
        {
            "action": {
                "type": "text",
                "payload": "{\"button\": \"2\"}",
                "label": "!Отзыв"
            },
            "color": "positive"
        }
    ]
    ]
}


def main():
    vk_session = vk_api.VkApi(
        token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, 193170178)
    fl = False
    message = 'Напишите команду "!Пожаловаться", чтобы пожаловаться\n команду ' \
              '"!Отзыв", чтобы оствить отзыв'
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            if event.obj.message['text'].lower() == '!пожаловаться':
                message = f'''Пожалуйста опишите что вам не понравилось'''
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=message,
                                 random_id=random.randint(0, 2 ** 64))
            elif event.obj.message['text'].lower() == '!отзыв':
                message = f'''Пожалуйста оставьте отзыв'''
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=message,
                                 random_id=random.randint(0, 2 ** 64))
            else:
                if message == 'Пожалуйста опишите что вам не понравилось':
                    message = 'Спасибо за ваш жалобу! Мы постараемся все исправить'
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=message,
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=str(json.dumps(keyboard)))
                    sessions = db_session.create_session()
                    com = complaint_book.Book()
                    com.vk_id = event.obj.message['from_id']
                    com.comment_text = event.obj.message['text']
                    com.type_of_message = 'complaints'
                    sessions.add(com)
                    sessions.commit()
                    message = 'Напишите команду "!Пожаловаться", чтобы пожаловаться\n команду' \
                              ' "!Отзыв", чтобы оствить отзыв'

                elif message == 'Пожалуйста оставьте отзыв':
                    message = 'Спасибо за ваш отзыв!'
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=message,
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=str(json.dumps(keyboard)))
                    sessions = db_session.create_session()
                    com = complaint_book.Book()
                    com.vk_id = event.obj.message['from_id']
                    com.comment_text = event.obj.message['text']
                    com.type_of_message = 'review'
                    sessions.add(com)
                    sessions.commit()
                    message = 'Напишите команду "!Пожаловаться", чтобы пожаловаться\n команду ' \
                              '"!Отзыв", чтобы оствить отзыв'
                else:
                    vk.messages.send(user_id=event.obj.message['from_id'],
                                     message=message,
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=str(json.dumps(keyboard)))


if __name__ == '__main__':
    db_session.global_init("db/blogs.sqlite")
    main()
