# U.S. Visa Appointment Checker and Rescheduler

This Python script automates the process of checking for earlier U.S. visa appointment dates and rescheduling if a suitable date is found.

## Features

- Automatically logs into the U.S. visa appointment website
- Checks for available appointment dates
- Compares available dates with your currently scheduled date
- Attempts to reschedule if an earlier date is found
- Sends notifications via email using SendGrid

## Requirements

- Python 3.x
- Selenium WebDriver
- ChromeDriver
- SendGrid account (optional, for email notifications)

## Installation

1. Clone this repository or download the script.
2. Install required Python packages:
   ```
   pip install -r > requirements.txt
   ```
3. Ensure ChromeDriver is installed and in your system PATH, or use the `webdriver_manager` as shown in the script.

## Configuration

Create a `config.ini` file in the same directory as the script with the following structure:

```ini
[USVISA]
USERNAME = your_email@example.com
PASSWORD = your_password
SCHEDULE_ID = your_schedule_id
MY_SCHEDULE_DATE = YYYY-MM-DD
COUNTRY_CODE = your_country_code
FACILITY_ID = your_facility_id

[SENDGRID]
SENDGRID_API_KEY = your_sendgrid_api_key

[CHROMEDRIVER]
LOCAL_USE = True
HUB_ADDRESS = http://your_selenium_hub_address:4444/wd/hub
```

Replace the placeholders with your actual information.

## Usage

Run the script with:

```
python main.py
```

The script will:
1. Log into the visa appointment website
2. Check for available dates
3. Compare available dates with your current appointment
4. Attempt to reschedule if an earlier date is found
5. Send a notification email if rescheduling is successful or if the script encounters issues

## Important Notes

- The script uses web scraping techniques, which may break if the website structure changes.
- Use this script responsibly and in accordance with the terms of service of the visa appointment website.
- Ensure you have permission to automate interactions with the website.
- The script includes a cooldown period to avoid overloading the server. Adjust `RETRY_TIME`, `EXCEPTION_TIME`, and `COOLDOWN_TIME` as needed.

## Disclaimer

This script is provided for educational purposes only. Use at your own risk. The authors are not responsible for any consequences resulting from the use of this script.
