import logging
import os
import time
from http import HTTPStatus

import requests
import telebot
from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN', default="secret_key")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', default="secret_key")
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', default=257178471)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

UNIVERSE_START = 1549962000


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def worng_token(token):
    logging.critical(
        f'Отсутствуют переменная окружения. {token}'
    )
    raise KeyError(
        f'Отсутствуют переменная окружения. {token}'
    )


def check_tokens():
    """Проверка на наличие необходимых токенов в файле переменных среды."""
    if (not PRACTICUM_TOKEN):
        worng_token(PRACTICUM_TOKEN)
    if (not TELEGRAM_TOKEN):
        worng_token(TELEGRAM_TOKEN)
    if (not TELEGRAM_CHAT_ID):
        worng_token(TELEGRAM_CHAT_ID)


def get_api_answer(timestamp):
    """Метод запроса api для получения данных о домашних заданиях."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
    except requests.RequestException as e:
        logging.error(e)
    if response.status_code != HTTPStatus.OK:
        raise ValueError(f'Код ответа: {response.status_code}')
    return response.json()


def check_response(response):
    """Метод проверка наличия ключей в словаре ответа на запрос."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Тип ответа не соответствует ожидаемому, тип: {type(response)}')
    if (not ('homeworks' in response)):
        logging.error('Необходимые ключи отсутствуют!')
        raise KeyError('Ключь отсутствует в словаре')
    if not isinstance(response['homeworks'], list):
        rsponse_type = response['homeworks']
        raise TypeError(
            'Тип ответа не соответствует ожидаемому,'
            f'тип: {type(rsponse_type)}'
        )


def send_message(bot, message):
    """Метод отправки сообщения ботом пользователю."""
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id, message)
    except telebot.apihelper.ApiException as e:
        logging.error(e)
    else:
        logging.debug(
            f"Сообщение отправлено:chat_id={chat_id}, message={message}")


def parse_status(homework):
    """Метод парсинга окончательного письма пользователю."""
    if 'homework_name' not in homework:
        logging.error(
            "Отсутствует ключ 'homework_name' в словаре"
        )
        raise KeyError("Отсутствует ключ 'homework_name' в словаре")

    if 'status' not in homework:
        logging.error(
            "Отсутствует ключ 'status' в словаре"
        )
    name = homework['homework_name']
    status = homework['status']
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError('Неизвестный статус')
    verdict = HOMEWORK_VERDICTS[status]
    message = f'Изменился статус проверки работы "{name}". {verdict}'
    return message


def main():
    """Основная логика работы бота."""
    check_tokens()
    timestamp_default = UNIVERSE_START
    timestamp = timestamp_default
    bot = TeleBot(TELEGRAM_TOKEN)
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response.get('homeworks'):
                parsed_status = parse_status(response['homeworks'][0])
                send_message(bot, parsed_status)
            else:
                logging.debug('Список изменений домашних работ пуст')
        finally:
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
    )
    main()
