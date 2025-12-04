import os
import random
import time
import pandas as pd
from itertools import zip_longest 
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Use undetected-chromedriver for anti-bot bypass
import undetected_chromedriver as uc
from selenium_stealth import stealth

# --- Configuration Variables ---
EMAIL = 'yourApolloEmail'
PASSWORD = 'your ApolloPassword'
URL = "https://app.apollo.io/#/lists/7899....." # Target List URL
LOGIN_BUTTON_XPATH = "//button[normalize-space()='Log In']"
CF_MODAL_XPATH = "//div[contains(@class, 'zp-modal-mask')]"
DASHBOARD_ELEMENT_XPATH = "//*[@id='main-app']"
# New, more stable selector for the list data table header (List Name)
DATA_HEADER_XPATH = "//div[normalize-space()='List Name']"
# New Selector for the main body of the data table (excluding the header)
TABLE_BODY_SELECTOR = 'div[role="rowgroup"]:not(.zp_BkjQG)'
# New Selector for pagination
NEXT_PAGE_BUTTON_CSS = 'button[aria-label="next page"]'
# -------------------------------

class ApolloScraper:
    def __init__(self, user_agents, url):
        '''Initialize the scraper with user agents, login credentials, and URL.'''
        self.user_agents = user_agents
        self.url = url
        self.driver = self.setup_webdriver()

    def setup_webdriver(self):
        '''Set up the Undetected Chrome WebDriver with stealth options.'''
        options = uc.ChromeOptions()
        options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        # options.add_argument("--headless")  # Uncomment if you want to run headlessly

        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()
        
        stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
        )
        return self.driver

    def login(self):
        '''Perform login, force navigation to the target list, and wait for readiness.'''
        self.driver.get(self.url)
        wait = WebDriverWait(self.driver, 60)

        try:
            # 1. Login Steps
            email_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
            email_input.send_keys(EMAIL)
            password_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
            password_input.send_keys(PASSWORD)
            log_in_button = wait.until(EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH)))
            log_in_button.click()

            # --- POST-LOGIN WAIT & NAVIGATION FIX ---
            # 2. Wait for the Cloudflare/Verifying modal to DISAPPEAR
            wait.until(EC.presence_of_element_located((By.XPATH, DASHBOARD_ELEMENT_XPATH)))
            print("Waiting for verification modal to disappear...")
            # Using the original XPATH to wait for invisibility
            wait.until(EC.invisibility_of_element_located((By.XPATH, CF_MODAL_XPATH)))
            
            # 3. CRITICAL FIX: Force navigation from the landing page to the specific list URL
            if self.driver.current_url != self.url:
                print(f"Redirecting from current page to target list: {self.url}")
                self.driver.get(self.url)
            
            # 4. FINAL WAIT: Wait for the list content header to appear
            print("Waiting for the final list page to stabilize...")
            # Assuming the DATA_HEADER_XPATH is a placeholder for a unique element on the page
            wait.until(EC.presence_of_element_located((By.XPATH, DATA_HEADER_XPATH)))
            time.sleep(3) # Short, final sleep for dynamic table data to load after the header is visible
            
            print("Successfully logged in and page is ready!")

        except TimeoutException:
            print("Login failed: Timeout waiting for elements, verification, or final page load.")
        except Exception as e:
            print(f"An unexpected error occurred during login: {e}")
            
    def get_text_or_default(self, element, default=''):
        '''Helper function to extract text from an element or return default if None.'''
        return element.text.strip() if element else default

    def scrape_data(self, num_pages_to_scrape, excel_file_path):
        '''Scrape data from the Apollo website using robust CSS selectors and save to an Excel file.'''
        page_num = 0
        
        # New selector for checking if data rows are present
        DATA_ROW_INDICATOR = (By.CSS_SELECTOR, f'{TABLE_BODY_SELECTOR} div[role="row"][aria-rowindex]')

        print("Starting to scrape! :)")
        
        # Wait for an actual data row
        data_wait = WebDriverWait(self.driver, 15)
        try:
            print("Confirming presence of data rows...")
            data_wait.until(EC.presence_of_element_located(DATA_ROW_INDICATOR))
        except TimeoutException:
            print("Confirmed list header is loaded, but no data rows appeared.")
            print("The specific list may be empty, or the data row selector is wrong.")
            return # Exit the function if no data loads

        # The loop can now assume the data is present
        while page_num < num_pages_to_scrape:
            page_num += 1
            print(f'Scraping page {page_num}/{num_pages_to_scrape}...')
            
            # Give a small buffer for new page content to load after navigation
            if page_num > 1:
                time.sleep(random.uniform(2, 4)) 

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Initialize the data dictionary for this page
            page_data = {
                'First Name': [],
                'Last Name': [],
                'Job Title': [],
                'Business Name': [],
                'Personal email': [],
                'Phone number': [],
                'Personal LinkedIn': [],
                'Company LinkedIn': [], # Set to N/A as it's not explicitly listed/scraped this way
                'Country': [],
                'Niche': [], # Combination of Industries and Keywords
                'Employee Count': [] # Added Employee Count as it's easily scrapable
            }

            # Find the container for all data rows (excluding the header row group)
            data_rows = soup.select(f'{TABLE_BODY_SELECTOR} div[role="row"][aria-rowindex]')
            
            if not data_rows:
                print("No data rows found on the current page. Ending scrape.")
                break

            # --- CORE EXTRACTION LOGIC: Iterate row-by-row for accurate alignment ---
            for row in data_rows:
                # 1. Name (in column 1)
                full_name_element = row.select_one('div[aria-colindex="1"] span.zp_pHNm5')
                full_name = full_name_element.text.strip() if full_name_element else 'N/A'
                
                parts = full_name.split(maxsplit=1)
                page_data['First Name'].append(parts[0] if parts and parts[0] != 'N/A' else 'N/A')
                page_data['Last Name'].append(parts[1] if len(parts) > 1 else 'N/A')

                # 2. Job Title (in column 2)
                job_title_element = row.select_one('div[aria-colindex="2"] div.zp_YGDgt span.zp_FEm_X')
                page_data['Job Title'].append(self.get_text_or_default(job_title_element, 'N/A'))

                # 3. Company Name (in column 3)
                company_name_element = row.select_one('div[aria-colindex="3"] span.zp_xvo3G')
                page_data['Business Name'].append(self.get_text_or_default(company_name_element, 'N/A'))
                
                # 4. Email (in column 4)
                email_element = row.select_one('div[aria-colindex="4"] span.zp_JTaUA')
                page_data['Personal email'].append(self.get_text_or_default(email_element, 'N/A'))
                
                # 5. Phone Number (in column 5)
                # Check for visible phone number text in the cell (if it loads)
                phone_element = row.select_one('div[aria-colindex="5"] div.zp__ruQE a:not(.zp_BCsLt)')
                phone_text = self.get_text_or_default(phone_element)
                
                # Fallback to check for "Request phone number" or simply mark as unavailable
                if not phone_text or 'request' in phone_text.lower():
                    page_data['Phone number'].append('Hidden/Unavailable')
                else:
                    page_data['Phone number'].append(phone_text)


                # 6. LinkedIn & Social Links (in column 7)
                # The person's LinkedIn link should contain /in/
                linkedin_person_link = row.select_one('div[aria-colindex="7"] a[data-href*="linkedin.com/in/"]')
                page_data['Personal LinkedIn'].append(linkedin_person_link.get('href') if linkedin_person_link else 'N/A')
                
                # Company LinkedIn is not directly scrapable from this cell
                page_data['Company LinkedIn'].append('N/A') 

                # 7. Location/Country (in column 9)
                location_element = row.select_one('div[aria-colindex="9"] button span.zp_FEm_X')
                page_data['Country'].append(self.get_text_or_default(location_element, 'N/A'))

                # 8. Employee Count (in column 10)
                employee_count_element = row.select_one('div[aria-colindex="10"] span.zp_Vnh4L')
                page_data['Employee Count'].append(self.get_text_or_default(employee_count_element, 'N/A'))
                
                # 9. Niche/Industries and Keywords (in column 11 and 12)
                # Industries in column 11
                industries_elements = row.select('div[aria-colindex="11"] span.zp_z4aAi')
                # Keywords in column 12
                keywords_elements = row.select('div[aria-colindex="12"] span.zp_z4aAi')
                
                # Combine all industries and keywords into a single string
                all_niches = [self.get_text_or_default(el) for el in industries_elements + keywords_elements]
                # Filter out the "+X" element at the end of some lists
                all_niches = [n for n in all_niches if not n.startswith('+') and n != 'N/A']
                page_data['Niche'].append(", ".join(all_niches) if all_niches else 'N/A')

            # Save the data for this page
            df = pd.DataFrame(page_data)
            self.save_to_excel(df, excel_file_path)

            # Proceed to next page if available
            if page_num < num_pages_to_scrape:
                try:
                    # 1. Use the more robust CSS selector for the next button
                    next_page_button = self.driver.find_element(By.CSS_SELECTOR, NEXT_PAGE_BUTTON_CSS)
                    # 2. Add a check for the button's disabled state before clicking (optional, but good)
                    if 'true' in next_page_button.get_attribute('aria-disabled'):
                        print("Next page button is disabled. Reached end of list.")
                        break
                        
                    next_page_button.click()
                except NoSuchElementException:
                    print("No next page button found or end of pagination reached.")
                    break
                
            else:
                print(f"Reached the maximum specified number of pages to scrape: {num_pages_to_scrape}.")


    def save_to_excel(self, df, excel_file_path):
        '''Save the scraped data to an Excel file. If file exists, it appends new data.'''
        if os.path.isfile(excel_file_path):
            existing_df = pd.read_excel(excel_file_path)
            # Use 'first' to keep the first occurrence, which is safer when appending
            df_no_duplicates = pd.concat([existing_df, df]).drop_duplicates(keep='first', ignore_index=True)
            df_no_duplicates.to_excel(excel_file_path, index=False)
        else:
            df.to_excel(excel_file_path, index=False)
        print(f"Data saved to {excel_file_path}")

    def remove_duplicates(self, input_file, output_file):
        '''Remove duplicate entries in the Excel file and save the cleaned data.'''
        if not os.path.exists(input_file):
            print(f"Cannot remove duplicates: Input file '{input_file}' not found.")
            return

        df = pd.read_excel(input_file)
        if df.duplicated().any():
            # Dropping duplicates and keeping the first one encountered is standard for cleaning
            df_no_duplicates = df.drop_duplicates(keep='first')
            df_no_duplicates.to_excel(output_file, index=False)
            print(f"Duplicate rows removed and saved to {output_file}")
        else:
            df.to_excel(output_file, index=False)
            print("No duplicate rows found. Data remains unchanged.")

    def quit(self):
        '''Close the WebDriver session, handling potential OS error on shutdown.'''
        try:
          self.driver.quit()
        except Exception as e:
        # Catch the specific OSError or a general exception on shutdown
         if "handle is invalid" in str(e):
            print("Successfully terminated browser process, ignoring handle error.")
        else:
            print(f"Error during browser shutdown: {e}")


if __name__ == "__main__":
    user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"]

    scraper = ApolloScraper(user_agents, URL)

    scraper.login()

    num_pages_to_scrape = 2  
    excel_file_path = 'data.xlsx'
    scraper.scrape_data(num_pages_to_scrape, excel_file_path)

    scraper.quit()

    output_file_path = "cleaned_data.xlsx"
    # FIX: Only attempt to remove duplicates if the data file exists
    if os.path.exists(excel_file_path):
        scraper.remove_duplicates(excel_file_path, output_file_path)
    else:
        print("Skipping duplicate removal as no data file was created.")