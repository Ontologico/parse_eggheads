import json
import os
import time
import traceback
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from conf import (
    accept_date_button_selector,
    adv_window_id,
    calendar_button_selector,
    card_info_class_name,
    driver_options,
    end_date,
    end_date_selector,
    input_search_id,
    save_every_n_companies,
    search_button_selector,
    search_el_class,
    start_date,
    start_date_selector,
)

load_dotenv(override=True)

bot_token = os.environ["BOT_TOKEN"]
chat_id = os.environ["CHAT_ID"]
egg_email = os.environ["EGG_EMAIL"]
egg_password = os.environ["EGG_PASSWORD"]


def egg_login(driver, email, password, login_url="https://eggheads.solutions/fe3/login"):
    """Функция для логина на eggheads"""

    driver.get(login_url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#js-authorization-login\\ qa-email"))
    )

    username_input = driver.find_element(By.CSS_SELECTOR, "#js-authorization-login\\ qa-email")
    username_input.send_keys(email)

    password_input = driver.find_element(By.CSS_SELECTOR, "#js-authorization-password")
    password_input.send_keys(password)

    password_input.send_keys(Keys.RETURN)
    WebDriverWait(driver, 10).until(EC.url_changes(login_url))
    return driver


def extract_indicator_value(indicator_id, soup):
    '''Функция извлечения значений из "карточек"'''
    indicator = soup.find("div", {"id": indicator_id})
    if indicator:
        value = indicator.find("div", class_="m-indicator-value")
        return value.get_text(strip=True) if value else None
    return None


# Функция для преобразования значений
def parse_value(value, value_type="currency"):
    if not value or "-" in value or "—" in value:
        return None
    if value_type == "currency":
        return int(value.replace("\xa0", "").replace("₽", "").strip())
    elif value_type == "percent":
        return float(value.replace("\xa0", "").replace("%", "").replace(",", ".").strip())
    elif value_type == "integer":
        return int(value.replace("\xa0", "").strip())
    return value


def iterate_months(start_date, end_date):
    """Возвращает итератор по месяцам"""
    # Преобразуем строки в объекты datetime
    current_date = datetime.strptime(start_date, "%Y-%m")
    end_date = datetime.strptime(end_date, "%Y-%m")

    while current_date <= end_date:
        # Первое число месяца
        first_day = current_date.replace(day=1)

        # Последнее число месяца
        next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        last_day = next_month - timedelta(days=1)

        yield first_day, last_day

        # Переходим к следующему месяцу
        current_date = next_month


def send_telegram_message(message):
    """Функция отправки сообщения через тг бота"""

    if not bot_token or not chat_id:
        logger.info("Telegram credentials not set in environment variables")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(message)
        logger.info("Telegram message sent successfully")
    except requests.exceptions.RequestException as e:
        logger.info(f"Failed to send Telegram message: {e}")


def start_parsing(save_path, source_path, reverse_flag, start_with=0):
    def init_driver():
        driver = webdriver.Firefox(options=driver_options)
        driver = egg_login(driver, email=egg_email, password=egg_password)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, search_button_selector)))
        return driver

    driver = init_driver()
    months_iterator = tuple(iterate_months(start_date, end_date))
    df = pd.DataFrame()

    ogrn_codes = pd.read_csv(source_path)["OGRN"].sort_values(ascending=reverse_flag)[start_with:]
    skipped_ogrn = []

    is_ever_ok = True
    total_records = 0

    for i, ogrn in tqdm(enumerate(ogrn_codes, start=start_with), total=len(skipped_ogrn)):
        try:
            try:
                ogrn = int(ogrn)
                driver.refresh()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, search_button_selector))
                )

                search_button = driver.find_element(by=By.CSS_SELECTOR, value=search_button_selector)
                search_button.click()
                search_button.click()

                input_search = driver.find_element(by=By.ID, value=input_search_id)
                driver.execute_script("arguments[0].scrollIntoView();", input_search)

                # wait = WebDriverWait(driver, 10)
                # input_search = wait.until(EC.visibility_of_element_located((By.ID, "js-e-search-input")))

                input_search.clear()
                input_search.send_keys(ogrn)
                try:
                    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, search_el_class)))
                except TimeoutException:
                    skipped_ogrn.append(ogrn)
                    continue

                input_search.send_keys(Keys.RETURN)
                driver.switch_to.window(driver.window_handles[-1])

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, calendar_button_selector))
                )
                calendar_button = driver.find_element(by=By.CSS_SELECTOR, value=calendar_button_selector)

                # Убираю окно, которое перекрывает кнопку:
                overlay = driver.find_element(By.ID, adv_window_id)
                if overlay.is_displayed():
                    driver.execute_script("arguments[0].style.display = 'none';", overlay)

                for start_date_i, end_date_i in months_iterator:
                    # Небольшой цикл, который нужен для открытия календаря
                    while True:
                        calendar_button.click()
                        start_date_input = driver.find_elements(by=By.CSS_SELECTOR, value=start_date_selector)
                        if start_date_input:
                            break
                        time.sleep(1)

                    start_date_input = driver.find_element(by=By.CSS_SELECTOR, value=start_date_selector)
                    end_date_input = driver.find_element(by=By.CSS_SELECTOR, value=end_date_selector)

                    start_date_input.clear()
                    start_date_input.send_keys(start_date_i.strftime("%Y-%m-%d"))
                    end_date_input.clear()
                    end_date_input.send_keys(end_date_i.strftime("%Y-%m-%d"))

                    accept_date_button = driver.find_element(by=By.CSS_SELECTOR, value=accept_date_button_selector)
                    accept_date_button.click()
                    # Жду появления информации на карточках:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, card_info_class_name))
                    )

                    soup = BeautifulSoup(driver.page_source, "html.parser")

                    # profit = extract_indicator_value("js-indicator-ordersPeriodSum", soup)
                    # if profit is None:
                    #     continue

                    data = {
                        "ОГРН": int(ogrn),
                        "Последний день": end_date_i.strftime("%Y-%m-%d"),
                        "Выручка по заказам FBO за 30 дней, руб": parse_value(
                            extract_indicator_value("js-indicator-ordersPeriodSum", soup),
                            "currency",
                        ),
                        "Потери FBO за 30 дней, руб": parse_value(
                            extract_indicator_value("js-indicator-loosesPeriodSum", soup),
                            "currency",
                        ),
                        "Потери FBO к выручке за 30 дней, %": parse_value(
                            extract_indicator_value("js-indicator-loosesPeriodPercent", soup),
                            "percent",
                        ),
                        "Товаров на последний день, шт": parse_value(
                            extract_indicator_value("js-indicator-totalProducts", soup),
                            "integer",
                        ),
                        "Продаётся за 30 дней, %": parse_value(
                            extract_indicator_value("js-indicator-orderedCardsCountPercent", soup),
                            "percent",
                        ),
                        "80% выручки за 30 дней, %": parse_value(
                            extract_indicator_value("js-indicator-groupAOrderedCardsCountPercent", soup),
                            "percent",
                        ),
                        "Средний чек товаров категории А за 30 дней, руб": parse_value(
                            extract_indicator_value("js-indicator-groupAAvgOrderSum", soup),
                            "currency",
                        ),
                    }

                    new_df = pd.DataFrame(data, index=[0])
                    df = pd.concat([df, new_df], ignore_index=True)

                total_records += 1
                if total_records % save_every_n_companies == 0:
                    df.to_csv(f"{save_path}/sel_data_{i}{'_rev' if reverse_flag else ''}")
                    with open(f"{save_path}/skipped_ogrn_{i}.json", "w+") as f:
                        json.dump(skipped_ogrn, f)
                    df = pd.DataFrame()

                if len(driver.window_handles) > 1:
                    driver.close()
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[0])

            except Exception as err:
                logger.error(f"Error processing OGRN {ogrn}: {str(err)}")
                traceback.print_exc()
                raise  # Перебрасываем исключение во внешний блок

        except Exception:
            df.to_csv(f"{save_path}/sel_data_{i}{'_rev' if reverse_flag else ''}")
            with open(f"{save_path}/skipped_ogrn_{i}.json", "w+") as f:
                json.dump(skipped_ogrn, f)
            df = pd.DataFrame()
            logger.error("Critical error occurred, reinitializing driver")
            try:
                driver.save_screenshot("exception_screen.png")
            except Exception as screenshot_err:
                logger.error(f"Failed to save screenshot: {screenshot_err}")

            try:
                driver.quit()
            except Exception as quit_err:
                logger.error(f"Error quitting driver: {quit_err}")

            try:
                driver = init_driver()
            except Exception:
                send_telegram_message("Не получается инициализировать драйвер")
            skipped_ogrn.append(ogrn)

            if not is_ever_ok:
                send_telegram_message("Something wrong...")
            is_ever_ok = False
            continue

        is_ever_ok = True
