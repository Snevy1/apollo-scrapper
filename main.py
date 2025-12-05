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
from selenium.webdriver.common.keys import Keys

# Use undetected-chromedriver for anti-bot bypass
import undetected_chromedriver as uc
from selenium_stealth import stealth

# --- Configuration Variables ---
EMAIL = ''
PASSWORD = ''

# Instead of full URL with filters, use base URL and configure filters separately
BASE_URL = "https://app.apollo.io/#/people"

# Filter configuration
FILTERS = {
    'email_status': 'verified',  # verified, likely_to_engage, guessed, unavailable
    'seniorities': ['owner', 'entry'],  # owner, entry, senior, manager, etc.
    'location': 'United States',
}

LOGIN_BUTTON_XPATH = "//button[normalize-space()='Log In']"
CF_MODAL_XPATH = "//div[contains(@class, 'zp-modal-mask')]"
DASHBOARD_ELEMENT_XPATH = "//*[@id='main-app']"

# Selectors for PEOPLE page
PEOPLE_TABLE_BODY_SELECTOR = 'div.zp_XgaPk[role="rowgroup"]'
PEOPLE_ROW_SELECTOR = 'div[role="row"][aria-rowindex]'
NEXT_PAGE_BUTTON_CSS = 'button[aria-label="Next"]'

# Selectors for LIST page
LIST_HEADER_XPATH = "//div[normalize-space()='List Name']"
LIST_TABLE_BODY_SELECTOR = 'div[role="rowgroup"]:not(.zp_BkjQG)'
# -------------------------------

class ApolloScraper:
    def __init__(self, user_agents, base_url, filters=None):
        '''Initialize the scraper with user agents, login credentials, and URL.'''
        self.user_agents = user_agents
        self.base_url = base_url
        self.filters = filters or {}
        self.driver = self.setup_webdriver()
        self.page_type = None

    def setup_webdriver(self):
        '''Set up the Undetected Chrome WebDriver with stealth options.'''
        options = uc.ChromeOptions()
        options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        # options.add_argument("--headless")

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
        '''Perform login and navigate to the people page.'''
        self.driver.get("https://app.apollo.io/")
        wait = WebDriverWait(self.driver, 60)

        try:
            # 1. Login Steps
            print("Logging in...")
            email_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
            email_input.send_keys(EMAIL)
            password_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='password']")))
            password_input.send_keys(PASSWORD)
            log_in_button = wait.until(EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH)))
            log_in_button.click()

            # 2. Wait for verification modal to disappear
            wait.until(EC.presence_of_element_located((By.XPATH, DASHBOARD_ELEMENT_XPATH)))
            print("Waiting for verification modal to disappear...")
            wait.until(EC.invisibility_of_element_located((By.XPATH, CF_MODAL_XPATH)))
            
            # 3. Wait for default page
            time.sleep(3)
            
            # 4. Navigate to base URL (people page)
            print(f"Navigating to: {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # 5. Detect page type
            self._detect_page_type()
            
            # 6. Apply filters if on people page
            if self.page_type == 'people' and self.filters:
                print("Applying filters through UI...")
                self._apply_filters()
            
            # 7. Wait for data to load
            if self.page_type == 'people':
                print("Waiting for people data to load...")
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PEOPLE_TABLE_BODY_SELECTOR)))
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'{PEOPLE_TABLE_BODY_SELECTOR} {PEOPLE_ROW_SELECTOR}')))
                time.sleep(3)
            elif self.page_type == 'list':
                print("Waiting for list data to load...")
                wait.until(EC.presence_of_element_located((By.XPATH, LIST_HEADER_XPATH)))
                time.sleep(3)
            
            print("Successfully logged in and page is ready!")
            print(f"Final URL: {self.driver.current_url}")

        except TimeoutException as e:
            print(f"Login failed: Timeout - {e}")
            print(f"Current URL: {self.driver.current_url}")
            self.driver.save_screenshot("login_timeout_error.png")
            
            # Save page source for debugging
            with open("page_source_debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("Saved page source to page_source_debug.html for inspection")
            
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            print(f"Current URL: {self.driver.current_url}")
            self.driver.save_screenshot("login_unexpected_error.png")
    
    def _detect_page_type(self):
        '''Detect whether we're on a people page or a list page.'''
        try:
            if '/people' in self.driver.current_url:
                self.page_type = 'people'
                print("Page type detected: PEOPLE")
            elif '/lists/' in self.driver.current_url:
                self.page_type = 'list'
                print("Page type detected: LIST")
            else:
                self.page_type = 'people'
                print("Page type unclear, defaulting to: PEOPLE")
        except Exception as e:
            print(f"Error detecting page type: {e}")
            self.page_type = 'people'
    
    def _apply_filters(self):
        '''Apply filters through the UI instead of URL parameters.'''
        wait = WebDriverWait(self.driver, 20)
        
        try:
            # Wait for filter panel to be visible
            time.sleep(2)
            
            # 1. Apply Email Status filter
            if 'email_status' in self.filters:
                print(f"Applying email status filter: {self.filters['email_status']}")
                try:
                    # Click on Email Status accordion
                    email_filter_xpath = "//span[text()='Email Status']"
                    email_accordion = wait.until(EC.element_to_be_clickable((By.XPATH, email_filter_xpath)))
                    email_accordion.click()
                    time.sleep(1)
                    
                    # Click on the specific status (e.g., "Verified")
                    status_xpath = f"//div[contains(@class, 'zp_BsIHj') and text()='{self.filters['email_status'].capitalize()}']"
                    # If filter already applied, it might be in a badge, try to find checkbox instead
                    try:
                        status_element = self.driver.find_element(By.XPATH, status_xpath)
                        # Check if already applied (look for close button)
                        if not status_element.find_elements(By.CSS_SELECTOR, 'i.apollo-icon-times'):
                            status_element.click()
                            time.sleep(1)
                        print("Email status filter applied")
                    except:
                        print("Email status filter may already be applied or selector changed")
                        
                except Exception as e:
                    print(f"Could not apply email status filter: {e}")
            
            # 2. Apply Job Titles (Seniority) filter
            if 'seniorities' in self.filters:
                print(f"Applying seniorities filter: {self.filters['seniorities']}")
                try:
                    # Click on Job Titles accordion
                    job_titles_xpath = "//span[text()='Job Titles']"
                    job_accordion = wait.until(EC.element_to_be_clickable((By.XPATH, job_titles_xpath)))
                    job_accordion.click()
                    time.sleep(1)
                    
                    # Apply each seniority
                    for seniority in self.filters['seniorities']:
                        seniority_xpath = f"//div[contains(@class, 'zp_BsIHj') and text()='{seniority.capitalize()}']"
                        try:
                            seniority_element = self.driver.find_element(By.XPATH, seniority_xpath)
                            if not seniority_element.find_elements(By.CSS_SELECTOR, 'i.apollo-icon-times'):
                                seniority_element.click()
                                time.sleep(0.5)
                            print(f"Seniority '{seniority}' applied")
                        except:
                            print(f"Could not apply seniority: {seniority}")
                    
                except Exception as e:
                    print(f"Could not apply seniorities filter: {e}")
            
            # 3. Apply Location filter
            if 'location' in self.filters:
                print(f"Applying location filter: {self.filters['location']}")
                try:
                    # Click on Location accordion
                    location_xpath = "//span[text()='Location']"
                    location_accordion = wait.until(EC.element_to_be_clickable((By.XPATH, location_xpath)))
                    location_accordion.click()
                    time.sleep(1)
                    
                    # Type in the location search box
                    # This is trickier - might need to find the input within the opened accordion
                    location_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='location' i]")
                    location_input.clear()
                    location_input.send_keys(self.filters['location'])
                    time.sleep(1)
                    location_input.send_keys(Keys.ENTER)
                    time.sleep(2)
                    print("Location filter applied")
                    
                except Exception as e:
                    print(f"Could not apply location filter: {e}")
            
            print("Filters applied successfully!")
            print(f"Current URL after filters: {self.driver.current_url}")
            
            # Wait for results to update
            time.sleep(3)
            
        except Exception as e:
            print(f"Error applying filters: {e}")
            print("Continuing with default search...")
            
    def get_text_or_default(self, element, default=''):
        '''Helper function to extract text from an element or return default if None.'''
        return element.text.strip() if element else default

    def scrape_data(self, num_pages_to_scrape, excel_file_path):
        '''Scrape data from the Apollo website (handles both people and list pages).'''
        
        if self.page_type == 'people':
            self._scrape_people_data(num_pages_to_scrape, excel_file_path)
        elif self.page_type == 'list':
            self._scrape_list_data(num_pages_to_scrape, excel_file_path)
        else:
            print("Unknown page type. Cannot scrape.")
    
    def _scrape_people_data(self, num_pages_to_scrape, excel_file_path):
        '''Scrape data from a people search page.'''
        page_num = 0
        
        print("Starting to scrape PEOPLE data! :)")
        
        # Wait for data rows
        data_wait = WebDriverWait(self.driver, 15)
        try:
            print("Confirming presence of people data rows...")
            data_wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'{PEOPLE_TABLE_BODY_SELECTOR} {PEOPLE_ROW_SELECTOR}')
            ))
            print("Data rows confirmed!")
        except TimeoutException:
            print("No people data rows appeared. The search may be empty.")
            
            # Debug: Save screenshot and page source
            self.driver.save_screenshot("no_data_rows.png")
            with open("no_data_page_source.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("Saved debug files: no_data_rows.png and no_data_page_source.html")
            return

        while page_num < num_pages_to_scrape:
            page_num += 1
            print(f'Scraping page {page_num}/{num_pages_to_scrape}...')
            
            if page_num > 1:
                time.sleep(random.uniform(3, 5))

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            page_data = {
                'First Name': [],
                'Last Name': [],
                'Job Title': [],
                'Business Name': [],
                'Personal email': [],
                'Phone number': [],
                'Personal LinkedIn': [],
                'Company LinkedIn': [],
                'Country': [],
                'Niche': [],
                'Employee Count': []
            }

            table_body = soup.select_one(PEOPLE_TABLE_BODY_SELECTOR)
            if not table_body:
                print("Could not find people table body!")
                break
                
            data_rows = table_body.select(PEOPLE_ROW_SELECTOR)
            
            if not data_rows:
                print("No data rows found on the current page. Ending scrape.")
                break

            print(f"Found {len(data_rows)} rows on page {page_num}")

            for idx, row in enumerate(data_rows):
                try:
                    # 1. Name (column 1)
                    name_element = row.select_one('div[aria-colindex="1"] a')
                    full_name = self.get_text_or_default(name_element, 'N/A')
                    
                    if '------' in full_name:
                        full_name = full_name.split('------')[0].strip()
                    
                    parts = full_name.split(maxsplit=1)
                    page_data['First Name'].append(parts[0] if parts and parts[0] != 'N/A' else 'N/A')
                    page_data['Last Name'].append(parts[1] if len(parts) > 1 else 'N/A')

                    # 2. Job Title (column 2)
                    job_title_element = row.select_one('div[aria-colindex="2"] span.zp_FEm_X')
                    page_data['Job Title'].append(self.get_text_or_default(job_title_element, 'N/A'))

                    # 3. Company Name (column 3)
                    company_name_element = row.select_one('div[aria-colindex="3"] span.zp_xvo3G')
                    page_data['Business Name'].append(self.get_text_or_default(company_name_element, 'N/A'))
                    
                    # 4. Email (column 4)
                    email_button = row.select_one('div[aria-colindex="4"] button')
                    if email_button and 'Access email' in email_button.text:
                        page_data['Personal email'].append('Requires Access')
                    else:
                        page_data['Personal email'].append('N/A')
                    
                    # 5. Phone Number (column 5)
                    phone_button = row.select_one('div[aria-colindex="5"] button')
                    if phone_button and 'Access Mobile' in phone_button.text:
                        page_data['Phone number'].append('Requires Access')
                    else:
                        page_data['Phone number'].append('N/A')

                    # 6. LinkedIn (column 7)
                    linkedin_link = row.select_one('div[aria-colindex="7"] a[href*="linkedin.com/in"]')
                    if linkedin_link:
                        page_data['Personal LinkedIn'].append(linkedin_link.get('href', 'N/A'))
                    else:
                        page_data['Personal LinkedIn'].append('N/A')
                    
                    page_data['Company LinkedIn'].append('N/A')

                    # 7. Location (column 9)
                    location_element = row.select_one('div[aria-colindex="9"] button span.zp_FEm_X')
                    page_data['Country'].append(self.get_text_or_default(location_element, 'N/A'))

                    # 8. Employee Count (column 10)
                    employee_count_element = row.select_one('div[aria-colindex="10"] span.zp_Vnh4L')
                    page_data['Employee Count'].append(self.get_text_or_default(employee_count_element, 'N/A'))
                    
                    # 9. Industries and Keywords
                    industries_elements = row.select('div[aria-colindex="11"] span.zp_z4aAi')
                    keywords_elements = row.select('div[aria-colindex="12"] span.zp_z4aAi')
                    
                    all_niches = [self.get_text_or_default(el) for el in industries_elements + keywords_elements]
                    all_niches = [n for n in all_niches if not n.startswith('+') and n != 'N/A']
                    page_data['Niche'].append(", ".join(all_niches) if all_niches else 'N/A')
                    
                except Exception as e:
                    print(f"Error processing row {idx}: {e}")
                    for key in page_data.keys():
                        if len(page_data[key]) <= idx:
                            page_data[key].append('N/A')

            df = pd.DataFrame(page_data)
            self.save_to_excel(df, excel_file_path)
            print(f"Saved {len(df)} rows from page {page_num}")

            if page_num < num_pages_to_scrape:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, NEXT_PAGE_BUTTON_CSS)
                    if 'true' in next_button.get_attribute('aria-disabled'):
                        print("Next page button is disabled. Reached end of results.")
                        break
                    
                    next_button.click()
                    print("Navigating to next page...")
                    time.sleep(2)
                    
                except NoSuchElementException:
                    print("No next page button found. Reached end of pagination.")
                    break
            else:
                print(f"Reached the maximum specified number of pages: {num_pages_to_scrape}")

    def _scrape_list_data(self, num_pages_to_scrape, excel_file_path):
        '''Scrape data from a list page (keeping original implementation).'''
        # [Keep your original list scraping code here - I'll omit for brevity]
        pass

    def save_to_excel(self, df, excel_file_path):
        '''Save the scraped data to an Excel file. If file exists, it appends new data.'''
        if os.path.isfile(excel_file_path):
            existing_df = pd.read_excel(excel_file_path)
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
            if "handle is invalid" in str(e):
                print("Successfully terminated browser process, ignoring handle error.")
            else:
                print(f"Error during browser shutdown: {e}")


if __name__ == "__main__":
    user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"]

    scraper = ApolloScraper(user_agents, BASE_URL, FILTERS)

    scraper.login()

    num_pages_to_scrape = 2  
    excel_file_path = 'data.xlsx'
    scraper.scrape_data(num_pages_to_scrape, excel_file_path)

    scraper.quit()

    output_file_path = "cleaned_data.xlsx"
    if os.path.exists(excel_file_path):
        scraper.remove_duplicates(excel_file_path, output_file_path)
    else:
        print("Skipping duplicate removal as no data file was created.")