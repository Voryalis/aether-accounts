Features
Automated Gmail Creation: Uses Selenium to automate the Gmail sign-up process.
Random User Details: Generates random Arabic names, user agents, and other details to create a unique account each time.
Proxy Support: Integrates with FreeProxy to avoid IP bans during account creation.
Randomized User Agent: Randomly chooses from a list of user agents to prevent detection by Gmail.
Logging and Debugging: Provides banners and notifications for ease of debugging and monitoring the process.
Requirements
Python 3.6 or higher
Google Chrome (Browser)
Chromedriver (Corresponding to your Chrome version)
Python Packages:
selenium
requests
unidecode
fp (FreeProxy)
To install the required packages, use the following command:

pip install selenium requests unidecode fp
Setup and Installation
Clone the Repository

git clone https://github.com/ShadowHackrs/Auto-Gmail-Creator.git
cd Auto-Gmail-Creator
Install Google Chrome and Chromedriver

Ensure Google Chrome is installed.
Download Chromedriver from Chromedriver's official website.
Place the chromedriver in your PATH or the root directory of the project.
Install Required Python Packages

pip install -r requirements.txt
Usage
Run the Script

Simply run the script using the command:
python3 auto_gmail_creator.py
The script will display a banner and start creating a Gmail account using randomly generated details.
Script Flow

Displays a custom banner with author information.
Launches Chrome in automated mode.
Uses a randomly chosen user agent for each session.
Connects to a proxy server to mask the IP address.
Creates an account with a randomly generated Arabic name and other details.
Configuration
Proxy Configuration: This script uses FreeProxy for handling proxies. To change proxy settings, refer to the FreeProxy documentation.
User Agents: User agents are stored in a list, and you can add or modify entries to improve randomization or cater to specific needs.
Code Overview
Here’s a breakdown of the main components:

Banner Display: A visual banner with ASCII art and author information.
Proxy Integration: Uses FreeProxy to fetch a proxy IP, reducing the chances of getting blocked.
User Agent Randomization: Randomly selects a user agent from the list to emulate various devices and browsers.
Account Creation: Uses Selenium commands to automate filling out the Gmail sign-up form.
Error Handling: Contains try-except blocks to manage common issues and delays to prevent detection.
Troubleshooting
Chromedriver Compatibility: Ensure that the version of Chromedriver matches your installed Chrome version.
Proxy Errors: Some proxies may be unreliable. Restart the script to fetch a new proxy if errors persist.
Element Not Found: If Gmail updates its sign-up form, some elements may need to be updated in the code.
Example Code Snippet
Here’s an example of how the script initializes the WebDriver:

options = ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")

# Set a random user agent
user_agent = random.choice(user_agents)
options.add_argument(f"user-agent={user_agent}")

# Set a proxy
proxy = FreeProxy().get()
options.add_argument(f"--proxy-server={proxy}")

driver = webdriver.Chrome(service=ChromeService(), options=options)
This code configures Chrome with a randomized user agent and proxy to improve anonymity.
