import os
import logging
import time
import requests

from dotenv import load_dotenv
import telebot
from telebot import TeleBot


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN', default="secret_key")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', default="secret_key")
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', default=247178471)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка на наличие необходимых токенов в файле переменных среды."""
    if (
        "PRACTICUM_TOKEN" in os.environ
        and "TELEGRAM_BOT_TOKEN" in os.environ
    ):
        logging.info('Проверка токенов завершена!')
        return True
    else:
        raise Exception(
            'Отсутствие одного или нескольких переменных окружения!'
        )


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
    if response.status_code != 200:
        raise Exception(f'Код ответа: {response.status_code}')
    response = response.json()
    return response


def check_response(response):
    """Метод проверка наличия ключей в словаре ответа на запрос."""
    if not isinstance(response, dict):
        raise TypeError('Тип ответа не соответствует ожидаемому')
    if (
        ('homeworks' in response)
        and ('current_date' in response)
    ):
        logging.info('Проверка наличия ключей завершена!')
    else:
        logging.error('Необходимые ключи отсутствуют!')
        raise KeyError('Ключь отсутствует в словаре')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Тип ответа не соответствует ожидаемому')

    if len(response['homeworks']) > 0:
        if 'status' in response['homeworks'][0]:
            logging.info('Ключь status в наличии')


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
    try:
        name = homework['homework_name']
        status = homework['status']
    except KeyError as e:
        logging.error(e)
    if status not in HOMEWORK_VERDICTS:
        raise KeyError('Неизвестный статус')
    verdict = HOMEWORK_VERDICTS[status]
    message = f'Изменился статус проверки работы "{name}". {verdict}'
    logging.warning(f'parse_status вернул: {message}')
    return message


def main():
    """Основная логика работы бота."""
    if (
        not PRACTICUM_TOKEN
        or not TELEGRAM_TOKEN
        or not TELEGRAM_CHAT_ID
    ):
        logging.critical(
            'Убедитесь, что заданы все обязательные переменные окружения: '
            'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID.'
        )
        raise Exception('Отсутствуют обязательные переменные окружения.')
    timestamp_default = 1549962000
    timestamp = timestamp_default
    bot = TeleBot(TELEGRAM_TOKEN)
    while True:
        check_tokens()
        response = get_api_answer(timestamp)
        check_response(response)
        if response.get('homeworks'):
            for homework in response['homeworks']:
                parsed_status = parse_status(homework)
                send_message(bot, parsed_status)
        else:
            logging.debug('Список изменений домашних работ пуст')
        timestamp = int(time.time())
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
