import time
import json
import random
import platform
import configparser
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

yatri_session_cookie = None
csrf_token = None
last_seen = None

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return {
        "username": config['USVISA']['USERNAME'],
        "password": config['USVISA']['PASSWORD'],
        "schedule_id": config['USVISA']['SCHEDULE_ID'],
        "my_schedule_date": config['USVISA']['MY_SCHEDULE_DATE'],
        "country_code": config['USVISA']['COUNTRY_CODE'],
        "facility_id": config['USVISA']['FACILITY_ID'],
        "sendgrid_api_key": config['SENDGRID']['SENDGRID_API_KEY'],
        "local_use": config['CHROMEDRIVER'].getboolean('LOCAL_USE'),
        "hub_address": config['CHROMEDRIVER']['HUB_ADDRESS']
    }


CONFIG = load_config()

STEP_TIME = 0.5
RETRY_TIME = 600
EXCEPTION_TIME = 1800
COOLDOWN_TIME = 3600
REGEX_CONTINUE = "//a[contains(text(),'Continuar')]"
EXIT = False

DATE_URL = f"https://ais.usvisa-info.com/{CONFIG['country_code']}/niv/schedule/{CONFIG['schedule_id']}/appointment/days/{CONFIG['facility_id']}.json?appointments[expedite]=false"
TIME_URL = f"https://ais.usvisa-info.com/{CONFIG['country_code']}/niv/schedule/{CONFIG['schedule_id']}/appointment/times/{CONFIG['facility_id']}.json?date=%s&appointments[expedite]=false"
APPOINTMENT_URL = f"https://ais.usvisa-info.com/{CONFIG['country_code']}/niv/schedule/{CONFIG['schedule_id']}/appointment"


def send_notification(msg):
    print(f"Sending notification: {msg}")

    if CONFIG['sendgrid_api_key']:
        message = Mail(
            from_email="marlondevjs@gmail.com",
            to_emails="myepes82@misena.edu.co",
            subject=msg,
            html_content=msg)
        try:
            sg = SendGridAPIClient(CONFIG['sendgrid_api_key'])
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)


def get_driver():
    if CONFIG['local_use']:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    else:
        driver = webdriver.Remote(command_executor=CONFIG['hub_address'], options=webdriver.ChromeOptions())
    return driver


driver = get_driver()


def login():
    driver.get(f"https://ais.usvisa-info.com/{CONFIG['country_code']}/niv")
    time.sleep(STEP_TIME)
    driver.find_element(By.XPATH, '//a[@class="down-arrow bounce"]').click()
    time.sleep(STEP_TIME)

    print("Login start...")
    driver.find_element(By.XPATH, '//*[@id="header"]/nav/div[1]/div[1]/div[2]/div[1]/ul/li[3]/a').click()
    time.sleep(STEP_TIME)
    Wait(driver, 60).until(EC.presence_of_element_located((By.NAME, "commit")))

    driver.find_element(By.XPATH, '//a[@class="down-arrow bounce"]').click()
    time.sleep(STEP_TIME)

    do_login_action()


def do_login_action():
    print("\tinput email")
    driver.find_element(By.ID, 'user_email').send_keys(CONFIG['username'])
    time.sleep(random.randint(1, 3))

    print("\tinput pwd")
    driver.find_element(By.ID, 'user_password').send_keys(CONFIG['password'])
    time.sleep(random.randint(1, 3))

    print("\tclick privacy")
    driver.find_element(By.CLASS_NAME, 'icheckbox').click()
    time.sleep(random.randint(1, 3))

    print("\tcommit")
    driver.find_element(By.NAME, 'commit').click()
    time.sleep(random.randint(1, 3))

    Wait(driver, 60).until(EC.presence_of_element_located((By.XPATH, REGEX_CONTINUE)))
    print("\tlogin successful!")

def get_user_actions():
    try:
        continue_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Continuar')]"))
        )
    
        continue_link.click()
        
        WebDriverWait(driver, 10).until(
            EC.url_to_be("https://ais.usvisa-info.com/es-mx/niv/schedule/56540884/continue_actions")
        )
        
        print("Se ha hecho clic en el botón 'continuar' y se ha cargado la siguiente página.")
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")

def schedule_action():
    global yatri_session_cookie, csrf_token
    try:
        # Navega directamente a la URL de la página de la cita
        driver.get("https://ais.usvisa-info.com/es-mx/niv/schedule/56540884/appointment")

        # Espera a que la URL de la página se cargue completamente
        WebDriverWait(driver, 10).until(
            EC.url_to_be("https://ais.usvisa-info.com/es-mx/niv/schedule/56540884/appointment")
        )

        # Obtener la cookie específica '_yatri_session'
        yatri_session_cookie = driver.get_cookie('_yatri_session')

        # Obtener el CSRF Token de una meta tag o un elemento del DOM
        csrf_token_element = driver.find_element(By.XPATH, "//meta[@name='csrf-token']")
        csrf_token = csrf_token_element.get_attribute("content")

        if yatri_session_cookie:
            print(f"Cookie '_yatri_session' encontrada")
        else:
            print("Cookie '_yatri_session' no encontrada.")

        if csrf_token:
            print(f"CSRF Token encontrado: {csrf_token}")
        else:
            print("CSRF Token no encontrado.")
        
        print("Se ha navegado a la página de la cita.")
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")

def get_date():
    global yatri_session_cookie, csrf_token
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "ais.usvisa-info.com",
        "If-None-Match": 'W/"daa83ddd615d08e2fcc7c7394a28a260"',
        "Referer": "https://ais.usvisa-info.com/es-mx/niv/schedule/56540884/appointment",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "X-CSRF-Token": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }
    
    if yatri_session_cookie:
        cookies = {
            '_yatri_session': yatri_session_cookie['value']
        }
    else:
        print("Cookie '_yatri_session' no encontrada.")
        return None

    try:
        # Realiza el llamado GET a la URL con los headers y cookies definidos
        response = requests.get(DATE_URL, headers=headers, cookies=cookies)
        
        if response.status_code == 200:
            content = response.text
            return json.loads(content)
        else:
            print(f"Error al hacer la solicitud: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ha ocurrido un error: {e}")
        return None

def get_time(date):
    driver.get(TIME_URL % date)
    content = driver.find_element(By.TAG_NAME, 'pre').text
    data = json.loads(content)
    time = data.get("available_times")[-1]
    print(f"Got time successfully! {date} {time}")
    return time

def reschedule(date):
    global EXIT
    print(f"Starting Reschedule ({date})")

    time = get_time(date)
    driver.get(APPOINTMENT_URL)

    data = {
        "utf8": driver.find_element(by=By.NAME, value='utf8').get_attribute('value'),
        "authenticity_token": driver.find_element(by=By.NAME, value='authenticity_token').get_attribute('value'),
        "confirmed_limit_message": driver.find_element(by=By.NAME, value='confirmed_limit_message').get_attribute('value'),
        "use_consulate_appointment_capacity": driver.find_element(by=By.NAME, value='use_consulate_appointment_capacity').get_attribute('value'),
        "appointments[consulate_appointment][facility_id]": CONFIG['facility_id'],
        "appointments[consulate_appointment][date]": date,
        "appointments[consulate_appointment][time]": time,
    }

    headers = {
        "User-Agent": driver.execute_script("return navigator.userAgent;"),
        "Referer": APPOINTMENT_URL,
        "Cookie": "_yatri_session=" + driver.get_cookie("_yatri_session")["value"]
    }

    response = requests.post(APPOINTMENT_URL, headers=headers, data=data)
    if 'Successfully Scheduled' in response.text:
        msg = f"Rescheduled Successfully! {date} {time}"
        send_notification(msg)
        EXIT = True
    else:
        msg = f"Reschedule Failed. {date} {time}"
        send_notification(msg)

def is_logged_in():
    return "error" not in driver.page_source


def print_dates(dates):
    print("Available dates:")
    for date in dates:
        print(f"{date.get('date')} \t business_day: {date.get('business_day')}")
    print()


def get_available_date(dates):
    global last_seen

    def is_earlier(date):
        my_date = datetime.strptime(CONFIG['my_schedule_date'], "%Y-%m-%d")
        new_date = datetime.strptime(date, "%Y-%m-%d")
        result = my_date > new_date
        print(f'Is {my_date} > {new_date}:\t{result}')
        return result

    print("Checking for an earlier date:")
    for d in dates:
        date = d.get('date')
        if is_earlier(date) and date != last_seen:
            _, month, day = date.split('-')
            if int(month) == 11 and int(day) >= 5:
                last_seen = date
                return date


if __name__ == "__main__":
    login()
    get_user_actions()
    schedule_action()
    retry_count = 0
    while 1:
        if retry_count > 6:
            break
        try:
            print("------------------")
            print(datetime.today())
            print(f"Retry count: {retry_count}")
            print()

            dates = get_date()[:5]
            if not dates:
              msg = "List is empty"
              send_notification(msg)
              EXIT = True
            print_dates(dates)
            date = get_available_date(dates)
            print()
            print(f"New date: {date}")
            if date:
                print("Rescheduling...")
                # reschedule(date)

            if(EXIT):
                print("------------------exit")
                break

            if not dates:
              msg = "List is empty"
              send_notification(msg)
              #EXIT = True
              time.sleep(COOLDOWN_TIME)
            else:
              time.sleep(RETRY_TIME)

        except:
            retry_count += 1
            time.sleep(EXCEPTION_TIME)

    if(not EXIT):
        send_notification("HELP! Crashed.")
    