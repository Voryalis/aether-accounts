"""
Gmail account registration automation.

Features
========
- Automated Gmail creation via Selenium with randomized data.
- Random Arabic names, user agents, and device UUIDs per session.
- Proxy support via FreeProxy to reduce IP bans.
- Headless-friendly Chrome flags to lower crash risk.
- Runtime banner and configuration logging for clarity and debugging.
- Attribution banner with author and repository details.
- Fresh, temporary Chrome profiles per account to avoid session conflicts, cleaned
  up automatically after each run.
- Optional `CHROME_BINARY` environment variable if Chrome needs an explicit path
  (use the full executable path like ``C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe``);
  a directory path is also accepted when it contains ``chrome.exe``/``chrome``.
- Optional `HEADLESS` environment variable (`0`/`false` to disable headless).
- Version detection for Chrome and ChromeDriver uses short timeouts and warnings
  to avoid hangs when binaries cannot report versions cleanly.

Requirements
------------
- Python 3.8 or newer.
- Google Chrome (or Chromium) installed locally.
- ChromeDriver that matches your Chrome version available on PATH (or set
  ``CHROMEDRIVER`` to its location); the Chrome and ChromeDriver major versions
  should match to avoid ``DevToolsActivePort`` crashes.
- Python packages: ``selenium``, ``requests``, ``unidecode``, ``fp``.
  Install with ``pip install selenium requests unidecode fp``.
  If Chrome is not on PATH, set ``CHROME_BINARY`` to its full location (for example
  ``C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe``). A directory
  path also works if it contains the executable.
  To add Chrome to PATH instead, append the folder containing ``chrome``/``chrome.exe``
  to PATH (for example on Windows, run `setx PATH "%PATH%;C:\\Program Files\\Google\\Chrome\\Application"`
  in an elevated shell; on Linux/macOS add `export PATH="$PATH:/usr/bin"` or your
  install directory to your shell profile). Likewise, set ``CHROMEDRIVER`` to the
  full path of your ChromeDriver executable if it is not already on PATH.

Usage
-----
    python autoreg.py [NUMBER_OF_ACCOUNTS]

If the argument is omitted, five accounts will be attempted. Proxy selection
is randomized; if no proxy can be acquired, a direct connection is used. The
script prints a startup banner so you can confirm it is running with the
expected configuration. Set ``HEADLESS=0`` in your environment to disable
headless mode for debugging.

Setup checklist
---------------
1. Install Python 3.8+ and the packages ``selenium``, ``requests``, ``unidecode``, ``fp``
   (``pip install selenium requests unidecode fp``).
2. Install Google Chrome/Chromium and a matching ChromeDriver; place them on PATH or
   set ``CHROME_BINARY``/``CHROMEDRIVER`` to their locations. The Chrome and
   ChromeDriver **major versions must match** to avoid ``DevToolsActivePort`` crashes.
3. (Optional) Set ``HEADLESS=0`` to watch the browser. Leave it unset for headless
   mode.
4. (Optional) Adjust the proxy logic in ``get_working_proxy`` if you want to supply
   your own proxy list instead of using ``FreeProxy``.
5. Close any running Chrome sessions before starting to avoid profile lock
   warnings on some platforms.

Author and Source
-----------------
    Author: Voryalis
    Repo: https://github.com/Voryalis
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Iterable, Optional

from fp.fp import FreeProxy
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from unidecode import unidecode


USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 YaBrowser/21.8.1.468 Yowser/2.5 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (X11; CrOS x86_64 14440.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4807.0 Safari/537.36",
    "Mozilla/5.0 (X11; CrOS x86_64 14526.69.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.82 Safari/537.36",
]

ARABIC_FIRST_NAMES: list[str] = [
    "Ali",
    "Ahmed",
    "Omar",
    "Youssef",
    "Ayman",
    "Khaled",
    "Salma",
    "Nour",
    "Rania",
    "Hassan",
    "Fadi",
    "Sara",
    "Fatma",
    "Heba",
    "Lina",
    "Rami",
    "Amir",
    "Yasmin",
    "Hala",
    "Tamer",
    "Mohammed",
    "Yasser",
    "Sami",
    "Amira",
    "Zain",
    "Khalil",
    "Nabil",
    "Ziad",
    "Farah",
    "Layla",
    "Jamal",
    "Hadi",
    "Tariq",
    "Mahmoud",
    "Ranya",
    "Rashed",
    "Alaa",
    "Kareem",
    "Basma",
    "Nadia",
    "Yasmeen",
    "Hussain",
    "Saeed",
    "Iman",
    "Reem",
    "Joud",
    "Nourhan",
    "Khadija",
    "Sahar",
    "Maya",
    "Tala",
    "Hiba",
    "Dalia",
    "Nisreen",
    "Mariam",
    "Haneen",
    "Wissam",
    "Amani",
    "Ibtihaj",
    "Khalida",
    "Dania",
    "Loubna",
    "Hanan",
    "Nora",
    "Rawan",
    "Salim",
    "Fouzia",
    "Zayna",
    "Adnan",
    "Jawad",
    "Mansour",
    "Waleed",
    "Zuhair",
    "Hisham",
    "Ibrahim",
    "Samira",
    "Huda",
    "Hossain",
    "Layal",
    "Kareema",
    "Zaki",
    "Aliya",
    "Salah",
    "Safaa",
    "Marwan",
    "Dina",
    "Asma",
    "Naima",
    "Tamara",
    "Tania",
    "Sabah",
    "Mona",
    "Firas",
    "Zayd",
    "Taha",
    "Yasin",
    "Sakina",
    "Rasha",
    "Sufyan",
    "Nafisa",
    "Othman",
    "Safa",
    "Nabilah",
    "Hala",
    "Faten",
    "Aisha",
    "Zainab",
    "Nouran",
    "Raneem",
]

ARABIC_LAST_NAMES: list[str] = [
    "Mohamed",
    "Ahmed",
    "Hussein",
    "Sayed",
    "Ismail",
    "Abdallah",
    "Khalil",
    "Soliman",
    "Nour",
    "Kamel",
    "Samir",
    "Ibrahim",
    "Othman",
    "Fouad",
    "Zaki",
    "Gamal",
    "Farid",
    "Mansour",
    "Adel",
    "Salem",
    "Hossam",
    "Nasser",
    "Qassem",
    "Khatib",
    "Rashed",
    "Moussa",
    "Naim",
    "Abdulaziz",
    "Anwar",
    "Younes",
    "Osama",
    "Bilal",
    "Fahd",
    "Rami",
    "Abdulrahman",
    "Maher",
    "Salim",
    "Tariq",
    "Amjad",
    "Ibtisam",
    "Sami",
    "Laith",
    "Saif",
    "Alaa",
    "Mujahid",
    "Hadi",
    "Attar",
    "Said",
    "Jabari",
    "Ashraf",
    "Abu",
    "Ali",
    "Nasr",
    "Darwish",
    "Azzam",
    "Yasin",
    "Zidan",
    "Farhan",
    "Khaled",
    "Mahmoud",
    "Qureshi",
    "Sheikh",
    "Abdulkareem",
    "Sharif",
    "Abdelaziz",
    "Yunus",
    "Hasan",
    "Shakir",
    "Musa",
    "Taha",
    "Khalaf",
    "Karim",
    "Rashid",
    "Siddiqi",
    "Sulaiman",
    "Almasri",
    "Alhussein",
    "Tarek",
    "Noor",
    "Husseini",
    "Jamil",
    "Ramzi",
    "Khalifa",
    "Hamed",
    "Anis",
    "Mahdi",
    "Wahab",
    "Bakkar",
    "Najib",
    "Abdulhadi",
    "Alhaj",
    "Shahrani",
    "Sulieman",
    "Majeed",
    "Nazari",
    "Saber",
    "Tawfiq",
    "Sabry",
    "Sharif",
]

DEFAULT_BIRTHDAY = "02 04 1950"
DEFAULT_GENDER = "1"  # Male
DEFAULT_PASSWORD = "P@ssw0rd42!"
DEFAULT_ACCOUNT_COUNT = 5
EMAILS_FILE = Path("emails.txt")
AUTHOR = "Voryalis"
PROJECT_URL = "https://github.com/Voryalis"
BINARY_ENV_VAR = "CHROME_BINARY"
CHROMEDRIVER_ENV_VAR = "CHROMEDRIVER"
HEADLESS_ENV_VAR = "HEADLESS"
VERSION_CHECK_TIMEOUT = 5
MONTH_LABELS = {
    "1": "January",
    "2": "February",
    "3": "March",
    "4": "April",
    "5": "May",
    "6": "June",
    "7": "July",
    "8": "August",
    "9": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}
GENDER_LABELS = {
    "1": "Male",
    "2": "Female",
    "3": "Rather not say",
    "4": "Custom",
}
BANNER = r"""
    ___        __         _____             _       _____                _           _
   /   | ____ / /_____ _ / ___/__  ______ _(_)___  / ___/___  ______   (_)___  _____(_)____
  / /| |/ __ `/ __/ __ `/\\__ \/ / / / __ `/ / __ \\ \__ \/ _ \\/ ___/  / / __ \\/ ___/ / ___/
 / ___ / /_/ / /_/ /_/ /___/ / /_/ / /_/ / / / / /___/ /  __/ /     / / /_/ / /  / (__  )
/_/  |_\\__,_/\\__/\\__,_//____/\\__,_/\\__,_/_/_/ /_/____/\\___/_/     /_/\\____/_/  /_/____/
"""


def get_working_proxy() -> Optional[str]:
    """Retrieve a random proxy, falling back to direct connection on failure."""

    try:
        proxy = FreeProxy(rand=True, timeout=1).get()
        print(f"Using proxy: {proxy}")
        return proxy
    except Exception as proxy_error:  # noqa: BLE001 - log any proxy acquisition issue
        print(f"Failed to fetch proxy, using direct connection. Error: {proxy_error}")
        return None


def save_email_to_file(email: str, password: str) -> None:
    EMAILS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with EMAILS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"Gmail: {email}, Password: {password}\n")


def show_banner() -> None:
    """Print a startup banner to make it obvious the script is running."""

    print(BANNER)
    print("Gmail AutoReg")
    print(f"Author: {AUTHOR}")
    print(f"GitHub: {PROJECT_URL}")
    print("—" * 80)


def log_runtime_settings(accounts_to_create: int, password: str, proxy: bool, headless: bool) -> None:
    """Log the primary runtime configuration for transparency."""

    print(f"Requested accounts: {accounts_to_create}")
    print(f"Default password: {password}")
    print(
        "Headless Chrome enabled with randomized user agents."
        if headless
        else "Headless Chrome disabled; browser will be visible."
    )
    print(f"Proxy support: {'enabled (FreeProxy)' if proxy else 'disabled'}")


def _binary_from_directory(candidate: Path) -> Optional[Path]:
    """Return the Chrome executable inside a directory if present."""

    for name in ("chrome.exe", "chrome"):
        executable = candidate / name
        if executable.exists():
            return executable
    return None


def resolve_chrome_binary() -> tuple[Optional[Path], bool]:
    """Return a Chrome/Chromium binary path if one is discoverable.

    Preference order:
    1. `CHROME_BINARY` environment variable if it points to an existing file or a
       directory containing ``chrome.exe``/``chrome`` (useful for Windows paths
       like ``C:\\Program Files\\Google\\Chrome\\Application``).
    2. A list of common Chrome/Chromium install paths across Linux, macOS, and Windows.
    """

    env_value = os.getenv(BINARY_ENV_VAR)
    env_present = bool(env_value)
    if env_value:
        candidate = Path(env_value)
        if candidate.exists():
            if candidate.is_file():
                return candidate, env_present
            derived = _binary_from_directory(candidate)
            if derived:
                return derived, env_present

    candidates = (
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    )
    for raw_path in candidates:
        candidate = Path(raw_path)
        if candidate.exists():
            return candidate, env_present
    return None, env_present


def _version_from_executable(executable: str) -> tuple[Optional[str], Optional[str]]:
    """Return the version output for a binary and an optional warning.

    Some Chrome builds emit messages like ``"Opening in existing browser session"``
    instead of a version string. Treat those as warnings so we do not report a
    misleading version or false mismatch. A short timeout prevents hanging when
    the binary blocks during ``--version`` execution.
    """

    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=VERSION_CHECK_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return None, "Version lookup timed out"
    except OSError:
        return None, "Executable not found"

    output = (result.stdout.strip() or result.stderr.strip() or "").strip()
    normalized = output.lower()

    noisy_markers = (
        "opening in existing browser session",
        "please close any running instance",
    )
    if any(marker in normalized for marker in noisy_markers):
        return None, output or "Non-version output from executable"

    if result.returncode != 0 or not output:
        return None, output or "No version output"

    return output, None


def chrome_version(chrome_binary: Optional[Path]) -> tuple[Optional[str], Optional[str]]:
    if not chrome_binary:
        return None, None
    return _version_from_executable(str(chrome_binary))


def log_chrome_binary(
    chrome_binary: Optional[Path], env_present: bool, version: Optional[str], warning: Optional[str]
) -> None:
    """Log how Chrome will be located for this run."""

    if chrome_binary:
        version_note = f" ({version})" if version else ""
        print(f"Chrome binary: {chrome_binary}{version_note}")
        if warning:
            print(f"Chrome version note: {warning}")
    else:
        if env_present:
            print(
                "Chrome binary: CHROME_BINARY was set but not found. Check the path (file or directory)"
                " or add Chrome to PATH."
            )
        else:
            print(
                "Chrome binary: not explicitly set. Add Chrome to PATH or set CHROME_BINARY if Chrome crashes or isn't found."
            )


def resolve_chromedriver_binary() -> tuple[Optional[Path], bool]:
    """Locate ChromeDriver either via CHROMEDRIVER env var or PATH."""

    env_value = os.getenv(CHROMEDRIVER_ENV_VAR)
    env_present = bool(env_value)
    if env_value:
        candidate = Path(env_value)
        if candidate.exists():
            return candidate, env_present

    found = shutil.which("chromedriver")
    if found:
        return Path(found), env_present

    return None, env_present


def chromedriver_version(chromedriver_binary: Optional[Path]) -> tuple[Optional[str], Optional[str]]:
    if chromedriver_binary:
        return _version_from_executable(str(chromedriver_binary))
    discovered = shutil.which("chromedriver")
    if discovered:
        return _version_from_executable(discovered)
    return None, None


def log_chromedriver_binary(
    chromedriver_binary: Optional[Path], env_present: bool, version: Optional[str], warning: Optional[str]
) -> None:
    if chromedriver_binary:
        version_note = f" ({version})" if version else ""
        print(f"ChromeDriver: {chromedriver_binary}{version_note}")
        if warning:
            print(f"ChromeDriver version note: {warning}")
    else:
        if env_present:
            print(
                "ChromeDriver: CHROMEDRIVER was set but not found. Verify the path or add chromedriver to PATH."
            )
        else:
            print(
                "ChromeDriver: not found on PATH. Install ChromeDriver or set the CHROMEDRIVER environment variable to its full path."
            )


def headless_enabled() -> bool:
    """Return whether headless mode should be enabled based on `HEADLESS` env var.

    Any case-insensitive value of ``0``, ``false``, ``no``, or ``off`` disables
    headless mode so users can watch the browser for troubleshooting.
    """

    value = os.getenv(HEADLESS_ENV_VAR)
    if value is None:
        return True
    return value.strip().lower() not in {"0", "false", "no", "off"}


def generate_username() -> str:
    """Generate a realistic username from random names and digits."""

    first_name = random.choice(ARABIC_FIRST_NAMES)
    last_name = random.choice(ARABIC_LAST_NAMES)
    random_number = random.randint(1000, 9999)
    first_name_normalized = unidecode(first_name).lower()
    last_name_normalized = unidecode(last_name).lower()
    return f"{first_name_normalized}.{last_name_normalized}{random_number}"


def _normalize_numeric_value(value: str) -> str:
    """Strip leading zeros from numeric strings (e.g., '04' -> '4')."""

    try:
        return str(int(value))
    except ValueError:
        return value


def _select_dropdown(
    driver: webdriver.Chrome, element, value: str, *, text: Optional[str] = None
) -> None:
    """Select a dropdown option, supporting native <select> and custom widgets."""

    normalized_value = _normalize_numeric_value(value)
    if element.tag_name.lower() == "select":
        Select(element).select_by_value(normalized_value)
        return

    element.click()
    option_text = text or value
    option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@role='option' and (@data-value='{0}' or .//span[normalize-space()='{1}'])]"
                " | //span[normalize-space()='{1}']".format(normalized_value, option_text),
            )
        )
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
    try:
        option.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", option)
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)


def _click_first_clickable(
    driver: webdriver.Chrome,
    locators: list[tuple[str, str]],
    *,
    timeout: int = 12,
    poll: int = 2,
) -> Optional[object]:
    """Return the first clickable element found from the provided locators."""

    end_time = time.time() + timeout
    while time.time() < end_time:
        for locator in locators:
            try:
                return WebDriverWait(driver, poll).until(
                    EC.element_to_be_clickable(locator)
                )
            except TimeoutException:
                continue
    return None


def fill_form(
    driver: webdriver.Chrome,
    password: str,
    birthday: str = DEFAULT_BIRTHDAY,
    gender: str = DEFAULT_GENDER,
) -> None:
    """Fill Gmail registration form and persist credentials."""

    device_uuid = uuid.uuid4()
    username = generate_username()
    print(f"Using device UUID: {device_uuid}")

    driver.get(
        "https://accounts.google.com/signup/v2/createaccount?flowName=GlifWebSignIn&flowEntry=SignUp"
    )

    # Fill in the name fields
    first_name_field = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "firstName"))
    )
    last_name_field = driver.find_element(By.NAME, "lastName")
    first_name_field.clear()
    first_name_field.send_keys(username.split(".")[0])
    last_name_field.clear()
    last_name_field.send_keys(username.split(".")[1])

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[@type='button']//span[text()='Next']")
        )
    ).click()

    # Fill birthday and gender
    birthday_elements = birthday.split()
    birthday_day, birthday_month, birthday_year = birthday_elements
    normalized_month = _normalize_numeric_value(birthday_month)
    month_label = MONTH_LABELS.get(normalized_month, birthday_month)
    month_element = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "month"))
    )
    _select_dropdown(driver, month_element, normalized_month, text=month_label)
    day_field = driver.find_element(By.ID, "day")
    day_field.clear()
    day_field.send_keys(birthday_day)
    year_field = driver.find_element(By.ID, "year")
    year_field.clear()
    year_field.send_keys(birthday_year)
    gender_element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "gender"))
    )
    _select_dropdown(
        driver, gender_element, gender, text=GENDER_LABELS.get(gender, gender)
    )
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "VfPpkd-LgbsSe"))
    ).click()

    # Create custom email
    time.sleep(2)
    if driver.find_elements(By.ID, "selectionc4"):
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "selectionc4"))
        ).click()

    username_field = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "Username"))
    )
    username_field.clear()
    username_field.send_keys(username)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "VfPpkd-LgbsSe"))
    ).click()

    # Enter and confirm password
    password_field = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, "Passwd"))
    )
    password_field.clear()
    password_field.send_keys(password)
    confirm_passwd_div = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "confirm-passwd"))
    )
    password_confirmation_field = confirm_passwd_div.find_element(
        By.NAME, "PasswdAgain"
    )
    password_confirmation_field.clear()
    password_confirmation_field.send_keys(password)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "VfPpkd-LgbsSe"))
    ).click()

    # Skip phone number and recovery email if present
    try:
        skip_locators = [
            (By.XPATH, "//span[contains(text(),'Skip')]"),
            (By.XPATH, "//span[contains(text(),'Not now')]"),
            (By.XPATH, "//span[contains(text(),\"I don't want a phone number\")]"),
        ]
        skip_button = _click_first_clickable(driver, skip_locators, timeout=15, poll=2)
        if skip_button:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", skip_button)
            try:
                skip_button.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", skip_button)
        else:
            print("No phone number verification step.")
    except Exception as skip_error:  # noqa: BLE001 - optional step can be absent
        print(f"Skipped optional phone/recovery step due to: {skip_error}")

    # Agree to terms
    agree_locators = [
        (By.CSS_SELECTOR, "button span.VfPpkd-vQzf8d"),
        (By.XPATH, "//span[contains(text(),'I agree')]"),
        (By.XPATH, "//span[contains(text(),'Agree')]"),
    ]
    agree_button = _click_first_clickable(driver, agree_locators, timeout=15, poll=2)
    if agree_button:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", agree_button)
        try:
            agree_button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", agree_button)

    print(
        f"Your Gmail successfully created:\n{{\ngmail: {username}@gmail.com\npassword: {password}\n}}"
    )
    save_email_to_file(f"{username}@gmail.com", password)


def build_chrome_options(
    user_agent: str,
    proxy: Optional[str],
    chrome_binary: Optional[Path],
    headless: bool,
    user_data_dir: Optional[Path],
) -> ChromeOptions:
    options = ChromeOptions()
    options.add_argument("--disable-infobars")
    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    if chrome_binary:
        options.binary_location = str(chrome_binary)
    return options


def create_single_account(password: str, headless: bool) -> None:
    user_agent = random.choice(USER_AGENTS)
    proxy = get_working_proxy()
    chrome_binary, chrome_env_present = resolve_chrome_binary()
    chromedriver_binary, chromedriver_env_present = resolve_chromedriver_binary()
    chrome_version_label, chrome_version_warning = chrome_version(chrome_binary)
    chromedriver_version_label, chromedriver_version_warning = chromedriver_version(chromedriver_binary)
    print(f"User agent for this run: {user_agent}")
    print(f"Proxy in use: {proxy if proxy else 'direct connection'}")
    print(f"Headless mode: {'enabled' if headless else 'disabled'}")
    log_chrome_binary(
        chrome_binary, chrome_env_present, chrome_version_label, chrome_version_warning
    )
    log_chromedriver_binary(
        chromedriver_binary,
        chromedriver_env_present,
        chromedriver_version_label,
        chromedriver_version_warning,
    )
    temp_profile = Path(tempfile.mkdtemp(prefix="autoreg-profile-"))
    options = build_chrome_options(
        user_agent, proxy, chrome_binary, headless, user_data_dir=temp_profile
    )
    try:
        service = (
            ChromeService(executable_path=str(chromedriver_binary))
            if chromedriver_binary
            else ChromeService()
        )
        driver = webdriver.Chrome(options=options, service=service)
    except WebDriverException as exc:
        print(
            "Failed to start Chrome session. "
            "Ensure Chrome and ChromeDriver are installed and compatible."
        )
        print(f"Detailed error: {exc.msg}")
        if not chrome_binary:
            print(
                "Tip: set the CHROME_BINARY environment variable to the full Chrome/Chromium path"
                " if the browser cannot be located."
            )
        if not chromedriver_binary:
            print(
                "Tip: install ChromeDriver, place it on PATH, or set the CHROMEDRIVER environment"
                " variable to its full path to avoid version mismatches."
            )
        if chrome_version_label and chromedriver_version_label:
            print(
                f"Observed Chrome {chrome_version_label} vs ChromeDriver {chromedriver_version_label}; ensure major versions match."
            )
        return

    try:
        fill_form(driver, password)
    except Exception as exc:  # noqa: BLE001 - top-level automation safety
        print(f"Account creation failed during form fill: {exc}")
    finally:
        driver.quit()
        shutil.rmtree(temp_profile, ignore_errors=True)
    time.sleep(random.randint(5, 15))


def create_multiple_accounts(number_of_accounts: int, password: str, headless: bool) -> None:
    for attempt in range(1, number_of_accounts + 1):
        print(f"\nStarting account {attempt} of {number_of_accounts}")
        create_single_account(password, headless)


def parse_account_count(args: Iterable[str]) -> int:
    if not args:
        return DEFAULT_ACCOUNT_COUNT
    try:
        requested = int(next(iter(args)))
        return max(requested, 1)
    except (ValueError, StopIteration):
        print("Invalid number provided. Falling back to default (5) accounts.")
        return DEFAULT_ACCOUNT_COUNT


if __name__ == "__main__":
    show_banner()
    accounts_to_create = parse_account_count(sys.argv[1:])
    headless = headless_enabled()
    log_runtime_settings(accounts_to_create, DEFAULT_PASSWORD, proxy=True, headless=headless)
    create_multiple_accounts(accounts_to_create, DEFAULT_PASSWORD, headless=headless)
