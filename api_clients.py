import aiohttp
import logging
from decouple import config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = config("API_URL")

async def register_user(phone_number: str):
    """
    Реєстрація користувача через API.

    :param phone_number: Номер телефону користувача у форматі +380XXXXXXXXX
    :return: Дані нового користувача (id, phone_number, api_key) або підняття винятку.
    """
    url = f"{API_URL}registration/users/"
    payload = {"phone_number": phone_number}

    try:

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, json=payload) as response:
                logger.info("Відправлено POST-запит до API: %s, дані: %s", url, payload)
                logger.info("Статус відповіді: %s", response.status)

                if response.status in (200, 201):
                    data = await response.json()
                    logger.info("Успішна відповідь від API: %s", data)
                    return data
                elif response.status == 400:
                    error_detail = await response.json()
                    logger.warning("API повернуло помилку 400: %s", error_detail)
                    raise ValueError(error_detail.get("detail", "Помилка реєстрації: некоректні дані."))
                elif response.status == 500:
                    logger.error("API повернуло помилку 500: Внутрішня помилка сервера.")
                    raise ValueError("Внутрішня помилка сервера API.")
                else:
                    error_detail = await response.json()
                    logger.error("Невідома помилка. Статус: %s, Відповідь: %s", response.status, error_detail)
                    raise ValueError(error_detail.get("detail", "Неочікувана помилка виконання API."))

    except aiohttp.ClientError as e:
        logger.exception("Помилка під час звернення до API: %s", e)
        raise ValueError("Помилка підключення до сервера API.")

    except Exception as e:
        logger.exception("Непередбачена помилка: %s", e)
        raise ValueError("Непередбачена помилка виконання.")


import httpx

async def send_pdf_request_to_service(tg_id: str, api_key: str):
    url = f"{API_URL}tg_request/generate_pdf/?tg_id={tg_id}"

    headers = {
        "api-key": api_key
    }


    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers)

            if response.status_code == 200:
                result = response.json()
                pdf_filename = result.get("pdf_filename")
                pdf_base64 = result.get("pdf_base64")
                return pdf_filename, pdf_base64
            else:
                return None, f"Помилка: {response.text}"

        except Exception as e:
            return None, f"Сталася помилка при зверненні до сервісу: {str(e)}"