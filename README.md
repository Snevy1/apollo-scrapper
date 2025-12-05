# Apollo Web Scraper

This repository contains a Python-based web scraper designed to automate the extraction of business and professional data from Apollo. The scraper utilizes `Selenium` for dynamic web interaction and `BeautifulSoup` for parsing HTML, making it ideal for gathering information across multiple pages efficiently. The code is organized into a class structure for ease of use, scalability, and maintainability.

## Features

- **Login Automation**: Automatically logs in to Apollo with your credentials.
- **Data Extraction**: Scrapes essential information such as:
  - Business Name
  - Website
  - Industry (Niche)
  - Country
  - First and Last Names
  - Job Title
  - Phone Number
  - Personal and Company LinkedIn URLs
  - Personal Email
- **Multiple Pages Scraping**: Configurable to scrape data from multiple pages.
- **Data Export**: Saves the scraped data to an Excel file (`.xlsx` format).
- **Duplicate Removal**: Automatically removes duplicate entries from the final Excel file.
- **Randomized User Agents**: Uses a random user-agent header to prevent blocking and simulate human browsing behavior.

## Setup & Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/apollo-web-scraper.git
   cd apollo-web-scraper

2. python -m venv venv
  - source venv/bin/activate   # On macOS/Linux
  - venv\Scripts\activate      # On Windows
3. pip install -r requirements.txt 
4. - Download and set up the Chrome WebDriver that matches your Chrome version.
5. - Update the following in the code:
    - - Your Apollo login credentials (email and password).
    - The Apollo saved list URL you want to scrape.
    - The number of pages you want to scrape.

 # ⚠️ Note: Sometimes Apollo may prompt you with a Cloudflare checkbox to verify you are human. You may need to manually click this before the scraper continues. We have used undetected chrome browser but sometimes it fails so you must click the check manually

# ⚙️ Adjusting Scraping Mechanism: If Apollo’s UI changes, you may need to update the scrape_data function. Copy the structure of the relevant HTML elements (e.g., div, id, or class attributes) from Apollo’s website and modify the scraping logic accordingly.

# How to Use
  - Modify the scraper.py file with your Apollo credentials and target URL.
  - Run the script:
     python main.py

# The script will log in to Apollo, scrape the data, and save it to an Excel file (complete_data.xlsx). It will also generate a cleaned file with duplicates removed (output_file.xlsx).


Troubleshooting
# Here are some common issues and fixes:
 ## ChromeDriver not found / version mismatch
  - Ensure you’ve downloaded the ChromeDriver version that matches your installed Chrome browser.
  - Add the ChromeDriver executable to your system PATH or place it in the project folder.
  - Cloudflare human verification
  - Apollo may occasionally prompt you with a Cloudflare checkbox. Manually click the checkbox to continue scraping.
  - Login errors
  - Double-check your Apollo credentials in main.py.
  - If Apollo enforces 2FA or captcha, you may need to log in manually once before running the scraper.

 ## Scraping stops or misses data
   - Apollo’s UI may have changed. Inspect the page structure using browser developer tools (F12 → Inspect).
   - Update the scrape_data function with the correct HTML tags (div, id, class) copied from Apollo’s site.
   - Excel file not generated
   - Verify that the script has write permissions in the project directory.
   - Ensure openpyxl is installed (pip install openpyxl).
   - Blocked or throttled requests
   - Try reducing the scraping speed or increasing wait times between requests.
   - Rotate user agents (already implemented) or use a proxy if necessary.




