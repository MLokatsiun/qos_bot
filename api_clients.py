import aiohttp
import logging
from decouple import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = config("API_URL")
CLIENT_NAME = config("CLIENT_NAME")
CLIENT_PASSWORD = config("CLIENT_PASSWORD")

async def register_user(phone_number: str):

    url = f"{API_URL}registration/users/"
    payload = {"phone_number": phone_number}
    headers = {"client-name": CLIENT_NAME,
               "client-password": CLIENT_PASSWORD}

    try:

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(url, json=payload, headers=headers) as response:
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



async def send_request_to_api(tg_id: str, request_data: str, command: str, api_key: str, country: str):
    url = f"{API_URL}tg_request/generate_pdf/"

    headers = {
        "accept": "application/json",
        "api-key": api_key,
    }

    params = {
        "tg_id": tg_id,
        "request_data": request_data,
        "command": command,
        "country": country,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data
                else:
                    logger.error(f"Error {response.status}: {await response.text()}")
                    return {"error": f"Request failed with status {response.status}"}
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        return {"error": "An error occurred while making the request."}

import httpx

async def send_file_to_api(api_url: str, file_path: str, api_key: str):
    headers = {
        "accept": "application/json",
        "api-key": api_key,
    }
    files = {
        "file": (file_path, open(file_path, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, headers=headers, files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {"error": f"Помилка запиту до API: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"Помилка статусу відповіді: {e.response.status_code} - {e.response.text}"}
        finally:
            files["file"][1].close()

async def send_request_to_api_shd(tg_id: str, request_data: str, command: str, api_key: str):
    url = f"{API_URL}request/shd/"

    headers = {
        "accept": "application/json",
        "api-key": api_key,
    }

    params = {
        "tg_id": tg_id,
        "request_data": request_data,
        "command": command,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data
                else:
                    logger.error(f"Error {response.status}: {await response.text()}")
                    return {"error": f"Request failed with status {response.status}"}
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        return {"error": "An error occurred while making the request."}


async def send_file_to_api_shd(api_url: str, file_path: str, api_key: str):
    headers = {
        "accept": "application/json",
        "api-key": api_key,
    }
    files = {
        "file": (file_path, open(file_path, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, headers=headers, files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {"error": f"Помилка запиту до API: {e}"}
        except httpx.HTTPStatusError as e:
            return {"error": f"Помилка статусу відповіді: {e.response.status_code} - {e.response.text}"}
        finally:
            files["file"][1].close()

