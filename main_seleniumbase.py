import os
import time
import pandas as pd
from itertools import zip_longest
from bs4 import BeautifulSoup
from seleniumbase import Driver
import pyperclip
import pyautogui

EMAIL_PART = 'APOLLO EMAIL'
PASSWORD = 'aAPOLLO PASSWORD'
URL = "APOLLO LIST LINK"

class ApolloScraper:
    def __init__(self, user_agents, url):
        '''Initialize the scraper with user agents, login credentials, and URL.'''
        self.user_agents = user_agents
        self.url = url
        self.driver = self.setup_webdriver()

    def setup_webdriver(self):
        '''Set up the Chrome WebDriver with random user-agent headers.'''
        driver = Driver(uc=True, headless=False)
        # driver.maximize_window()
        return driver

    def login(self):
        '''Perform login to the Apollo website using email and password.'''
        self.driver.get(self.url)
        self.driver.wait_for_element("name=email", timeout=10)

        # VIDIT KAKO PORPRAVIT ZA EMAIL
        self.driver.execute_script("""
            var emailField = document.querySelector("input[name=email]");
            emailField.value = 'fcalus00@fesb.hr';
            emailField.dispatchEvent(new Event('input', { bubbles: true }));  // Trigger the input event
            emailField.dispatchEvent(new Event('change', { bubbles: true }));  // Trigger the change event
        """)
        
        self.driver.type("name=password", PASSWORD)
        self.driver.click('//button[contains(@class, "zp-button zp_GGHzP zp_ZUsLW")]')

        time.sleep(5)

        self.driver.uc_gui_click_captcha()

        time.sleep(10)

    def scrape_data(self, num_pages_to_scrape, excel_file_path):
        '''Scrape data from the Apollo website and save it to an Excel file.'''
        page_num = 0
        print("Starting to scrape! :)")

        while page_num < num_pages_to_scrape:
            page_num += 1
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            page_data = {
                'Business Name': [], 'Website': [], 'Niche': [], 'Country': [],
                'First Name': [], 'Last Name': [], 'Job Title': [], 'Phone number': [],
                'Personal email': [], 'Personal LinkedIn': [], 'Company LinkedIn': []
            }

            names = [name.text.split(maxsplit=1) for name in soup.find_all('div', class_='zp_xVJ20') if name.find('a')]
            first_name, last_name = zip_longest(*names, fillvalue='')

            websites = [a.get('href') for a in soup.find_all('a', class_='zp-link zp_OotKe')
                        if a.get('href') and not any(
                    social in a.get('href') for social in ["facebook", "linkedin", "twitter", "apollo", "Facebook"])]

            company_names = [name.text.strip() for name in soup.find_all('div', class_='zp_J1j17')]
            websites.extend(["Website not specified"] * (len(company_names) - len(websites)))

            company_linkedin_list = [a.get('href') for a in soup.find_all('a', class_='zp-link zp_OotKe')
                                     if "linkedin" in a.get('href') and "company" in a.get('href')]
            company_linkedin_list.extend(
                ["LinkedIn page not specified"] * (len(company_names) - len(company_linkedin_list)))

            titles = [title.text.strip() for title in soup.find_all('span', class_='zp_Y6y8d')[::3]]

            emails = [email.text.strip() for email in soup.find_all('div', class_='zp_jcL6a')]

            page_data['Business Name'].extend(company_names)
            page_data['Website'].extend(websites)
            page_data['First Name'].extend(first_name)
            page_data['Last Name'].extend(last_name)
            page_data['Job Title'].extend(titles)
            page_data['Personal email'].extend(emails)
            page_data['Company LinkedIn'].extend(company_linkedin_list)

            df = pd.DataFrame(page_data)
            self.save_to_excel(df, excel_file_path)

            if page_num < num_pages_to_scrape:
                try:
                    print(f'Scraping page {page_num}/{num_pages_to_scrape}.')
                    self.driver.click(
                        'xpath=//*[@id="main-app"]/div[2]/div/div/div[2]/div[2]/div/div[2]/div/div/div/div/div/div/div[2]/div/div[4]/div/div/div/div/div[3]/div/div[2]/button[2]')
                    time.sleep(3)
                except Exception:
                    print("No next page button found.")
                    break

    def save_to_excel(self, df, excel_file_path):
        '''Save the scraped data to an Excel file. If file exists, it appends new data.'''
        if os.path.isfile(excel_file_path):
            existing_df = pd.read_excel(excel_file_path)
            df_no_duplicates = pd.concat([existing_df, df]).drop_duplicates(keep='last')
            df_no_duplicates.to_excel(excel_file_path, index=False)
        else:
            df.to_excel(excel_file_path, index=False)
        print(f"Data saved to {excel_file_path}")

    def quit(self):
        '''Close the WebDriver session.'''
        self.driver.quit()


if __name__ == "__main__":
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"]

    scraper = ApolloScraper(user_agents, URL)
    scraper.login()
    scraper.scrape_data(2, 'data.xlsx')
    scraper.quit()
