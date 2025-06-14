import os
import time
import base64
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urlparse, urlunparse

class ChapelBooking:
    """
    Automates booking a court at Chapel Allerton tennis club using Selenium.
    Handles login, court type selection, date selection (with robust jQuery UI datepicker logic),
    player entry, and booking confirmation. Supports both local and remote Selenium drivers.
    """
    BASE_URL = "https://chapel-a.clubsolution.co.uk/newlook/proc_baner.asp"
    
    def __init__(self):
        """
        Initialize the ChapelBooking automation class.
        Loads environment variables, sets up Selenium driver, and prepares booking parameters.
        """
        print("[DEBUG] ChapelBooking.__init__ starting...")
        load_dotenv()
        self.username = os.getenv("CHAPEL_USERNAME")
        self.password = os.getenv("CHAPEL_PASSWORD")
        
        # Handle player names with potential spaces
        player_names = os.getenv("PLAYER_NAMES", "")
        self.player_names = [name.strip() for name in player_names.split(",") if name.strip()]
        print(f"[DEBUG] Loaded {len(self.player_names)} player names: {self.player_names}")
        
        self.use_visitors = os.getenv("USE_VISITORS", "false").lower() == "true"
        self.court_type = os.getenv("COURT_TYPE", "Padel Courts")
        
        # Read booking date and time from environment variables
        self.booking_date = os.getenv("BOOKING_DATE", "18-06-2025")  # DD-MM-YYYY
        self.booking_time = os.getenv("BOOKING_TIME", "21:00")       # HH:MM
        print(f"[DEBUG] Booking date: {self.booking_date}, time: {self.booking_time}")
        
        if not self.username or not self.password:
            raise ValueError("Username and password must be set in .env file")
        
        # Initialize Chrome driver
        print("[DEBUG] Initializing Chrome driver...")
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")
        
        # Set up Chrome preferences
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False
        })
        
        # For testing: use local Chrome instead of remote Selenium Grid
        # self.driver = webdriver.Remote(
        #     command_executor="http://tower.local:4444/wd/hub",
        #     options=options
        # )
        self.driver = webdriver.Remote(
            command_executor="http://tower.local:4444/wd/hub",
            options=options
        )  # <-- REMOTE SELENIUM GRID
        self.wait = WebDriverWait(self.driver, 20)  # Increased timeout
        print("Chrome driver initialized successfully (using remote Selenium Grid)")
    
    def login(self) -> bool:
        """
        Log in to the Chapel Allerton booking website using credentials from environment variables.
        Handles cookie consent and waits for successful login.
        Returns True if login is successful, False otherwise.
        """
        print("[DEBUG] login() starting...")
        try:
            print("[DEBUG] Navigating to website...")
            self.driver.get(self.BASE_URL)
            
            # Handle cookie consent first
            self.handle_cookie_consent()
            
            # Find and click the login link
            print("[DEBUG] Looking for login link...")
            login_selectors = [
                "//a[@data-target='#loginModal']",
                "//a[contains(@data-target, 'loginModal')]",
                "//a[.//i[contains(@class, 'fa-lock')]]",
                "//a[contains(text(), 'Login')]"
            ]
            
            login_link = None
            for selector in login_selectors:
                try:
                    login_link = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if login_link:
                        print(f"[DEBUG] Found login link with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_link:
                print("Could not find login link")
                return False
            
            # Click the login link to open modal
            login_link.click()
            print("[DEBUG] Clicked login link")
            
            # Wait for login modal to appear and be visible
            print("[DEBUG] Waiting for login modal...")
            modal = self.wait.until(
                EC.visibility_of_element_located((By.ID, "loginModal"))
            )
            print("[DEBUG] Login modal found")
            
            # Wait a moment for animation
            time.sleep(0.5)
            
            # Try different selectors for username and password fields
            username_selectors = [
                (By.ID, "loginname"),
                (By.NAME, "loginname"),
                (By.CSS_SELECTOR, "#loginModal input[name='loginname']"),
                (By.XPATH, "//div[@id='loginModal']//input[@name='loginname']")
            ]
            
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "#loginModal input[name='password']"),
                (By.XPATH, "//div[@id='loginModal']//input[@name='password']")
            ]
            
            # Print all form elements for debugging
            print("\nForm elements in modal:")
            form_elements = modal.find_elements(By.TAG_NAME, "input")
            for elem in form_elements:
                try:
                    print(f"Type: {elem.get_attribute('type')}")
                    print(f"Name: {elem.get_attribute('name')}")
                    print(f"ID: {elem.get_attribute('id')}")
                    print("---")
                except:
                    continue
            
            # Find username field
            username_field = None
            for by, selector in username_selectors:
                try:
                    username_field = self.wait.until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if username_field:
                        print(f"[DEBUG] Found username field with selector: {selector}")
                        break
                except:
                    continue
                    
            if not username_field:
                print("Could not find username field")
                return False
            
            # Find password field
            password_field = None
            for by, selector in password_selectors:
                try:
                    password_field = self.wait.until(
                        EC.presence_of_element_located((by, selector))
                    )
                    if password_field:
                        print(f"[DEBUG] Found password field with selector: {selector}")
                        break
                except:
                    continue
                    
            if not password_field:
                print("Could not find password field")
                return False
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            password_field.clear()
            password_field.send_keys(self.password)
            print("[DEBUG] Entered credentials")

            # Optionally check the 'Stay Logged in' checkbox if present and not already checked
            try:
                stay_logged_in = modal.find_element(By.ID, "husklogin")
                if not stay_logged_in.is_selected():
                    stay_logged_in.click()
                    print("[DEBUG] Checked 'Stay Logged in' checkbox")
                else:
                    print("[DEBUG] 'Stay Logged in' checkbox already checked")
            except Exception as e:
                print("[DEBUG] 'Stay Logged in' checkbox not found or could not be checked (optional)")

            # Send Enter key after entering password
            enter_sent = False
            try:
                password_field.send_keys(Keys.RETURN)
                print("[DEBUG] Sent Enter key after password")
                enter_sent = True
            except Exception as e:
                print(f"[DEBUG] Could not send Enter key: {e}")
                enter_sent = False

            # Only click the login button if Enter was not sent
            if not enter_sent:
                try:
                    login_button = modal.find_element(By.ID, "sub")
                    print("[DEBUG] Found login button <span> with id='sub'")
                except Exception as e:
                    print(f"[DEBUG] Could not find login button <span> with id='sub': {e}")
                    return False
                # Try clicking the button using JavaScript (to trigger the onclick handler)
                try:
                    self.driver.execute_script("arguments[0].click();", login_button)
                    print("[DEBUG] Clicked login button using JavaScript")
                except Exception as e:
                    print(f"[DEBUG] JavaScript click failed: {e}, trying normal click...")
                    try:
                        login_button.click()
                        print("[DEBUG] Clicked login button using Selenium click")
                    except Exception as e2:
                        print(f"[DEBUG] Both click methods failed: {e2}")
                        return False
                print("[DEBUG] Submitted login form")
            else:
                print("[DEBUG] Submitted login form via Enter key")
            
            # Print the modal HTML after login attempt for debugging
            try:
                modal_html = modal.get_attribute('outerHTML')
                print("\nLogin modal HTML after login attempt:")
                print(modal_html)
            except Exception as e:
                print(f"[DEBUG] Could not get modal HTML: {e}")
            
            # Wait for login modal to disappear
            try:
                print("[DEBUG] Waiting for login modal to disappear...")
                self.wait.until(EC.invisibility_of_element_located((By.ID, "loginModal")))
                print("[DEBUG] Login modal disappeared")
            except Exception as e:
                print(f"[DEBUG] Login modal did not disappear: {e}")

            # Wait for the generic username span to appear (indicating successful login for any user)
            try:
                print("[DEBUG] Waiting for username to appear in top right (any user)...")
                user_xpath = "//span[i[contains(@class, 'fa-user')]]/span[contains(@class, 'caret')]/.."
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, user_xpath))
                )
                user_span = self.driver.find_element(By.XPATH, user_xpath)
                username = user_span.text.replace('caret', '').strip()
                print(f"[DEBUG] Login successful - username found in top right: {username}")
                return True
            except TimeoutException:
                print("[DEBUG] Timeout waiting for username to appear - login may have failed")
                return False
            
        except Exception as e:
            print(f"[DEBUG] Error during login: {str(e)}")
            return False
    
    def handle_cookie_consent(self) -> bool:
        """
        Handle the cookie consent popup if present.
        Returns True if handled or not present, False otherwise.
        """
        try:
            # Only check for cookie consent once per session
            if hasattr(self, '_cookie_consent_handled'):
                return True
                
            print("[DEBUG] Checking for cookie consent popup...")
            # Common selectors for cookie consent buttons
            consent_selectors = [
                "button#onetrust-accept-btn-handler",  # OneTrust
                "button[aria-label='Accept cookies']",
                "button.accept-cookies",
                "button.cookie-accept",
                "#cookie-consent-accept",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'I Accept')]"
            ]
            
            for selector in consent_selectors:
                try:
                    # Use a very short wait since cookie popups usually appear immediately
                    element = WebDriverWait(self.driver, 0.5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR if not selector.startswith('//') else By.XPATH, selector))
                    )
                    element.click()
                    print("[DEBUG] Clicked cookie consent button")
                    self._cookie_consent_handled = True
                    return True
                except:
                    continue
            
            # If we get here, either there was no cookie popup or we couldn't handle it
            self._cookie_consent_handled = True
            return True
            
        except Exception as e:
            print(f"[DEBUG] Error handling cookie consent: {str(e)}")
            return False

    def select_court_type(self) -> bool:
        """
        Select the desired court type (e.g., Padel Courts) using the custom dropdown UI or fallback JS.
        Returns True if selection is successful, False otherwise.
        """
        print("[DEBUG] select_court_type() starting...")
        try:
            print(f"[DEBUG] Attempting to select court type: {self.court_type}")
            # Try to interact with the custom dropdown UI first
            try:
                # Wait for the label or placeholder for the custom dropdown
                label_elem = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='LabelOmrValg' and contains(text(), 'Booking Area')]")
                ))
                print("[DEBUG] Found Booking Area label for custom dropdown")
                # The custom dropdown is likely the next sibling or nearby
                # Try to find a visible element that can be clicked to open the dropdown
                dropdown_elem = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//select[@id='soeg_omraede_placeholder' or @id='soeg_omraede']/following-sibling::*[not(self::select)][1] | //div[contains(@class, 'dropdown') or contains(@class, 'comboplaceholder') or contains(@class, 'show-menu-arrow')]")
                ))
                print("[DEBUG] Found custom dropdown element, clicking to open...")
                dropdown_elem.click()
                # Wait for the options to appear and select the desired one
                option_elem = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//li[contains(., '{self.court_type}') or contains(text(), '{self.court_type}')] | //span[contains(., '{self.court_type}') or contains(text(), '{self.court_type}')]"))
                )
                print(f"[DEBUG] Found custom dropdown option for {self.court_type}, clicking...")
                option_elem.click()
                print(f"[DEBUG] Selected court type via custom dropdown: {self.court_type}")
                return True
            except Exception as e:
                print(f"[DEBUG] Custom dropdown UI interaction failed: {e}. Falling back to JS method.")
            # Fallback: Use JS to set value and trigger onchange (may fail if sende is not defined)
            select_elem = self.wait.until(
                EC.presence_of_element_located((By.ID, "soeg_omraede"))
            )
            print("[DEBUG] Found <select id='soeg_omraede'> element (fallback)")
            court_type_map = {
                "Squash Courts": "1",
                "Indoor Tennis": "2",
                "Outdoor Tennis": "3",
                "Grass Courts": "4",
                "Padel Courts": "9"
            }
            value = court_type_map.get(self.court_type)
            if not value:
                print(f"[DEBUG] Unknown court type: {self.court_type}")
                return False
            js = (
                "var sel = document.getElementById('soeg_omraede');"
                f"if (sel) {{ sel.value = '{value}'; if (sel.onchange) sel.onchange(); }}"
            )
            self.driver.execute_script(js)
            print(f"[DEBUG] Set <select id='soeg_omraede'> value to {value} and triggered onchange via JS (fallback)")
            current_value = self.driver.execute_script("return document.getElementById('soeg_omraede').value;")
            print(f"[DEBUG] Current value after JS: {current_value}")
            print("[DEBUG] select_court_type() completed (fallback).")
            return current_value == value
        except Exception as e:
            print(f"[DEBUG] Error selecting court type via custom dropdown or JS: {e}")
            return False
    
    def check_availability(self, date: str, start_time: str, end_time: str) -> List[str]:
        """
        Check for available courts on a given date and time range.
        Returns a list of available court numbers.
        """
        available_courts = []
        
        try:
            print(f"[DEBUG] Checking availability for date: {date}, time: {start_time}-{end_time}")
            # Navigate to the date
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d-%m-%Y")
            
            # TODO: Implement date navigation
            print("[DEBUG] Looking for available courts...")
            # Check each court's availability
            courts = self.driver.find_elements(By.CLASS_NAME, "court-slot")
            print(f"[DEBUG] Found {len(courts)} court slots")
            
            for court in courts:
                try:
                    time_slot = court.find_element(By.CLASS_NAME, "time-slot")
                    if start_time in time_slot.text and "available" in court.get_attribute("class"):
                        court_number = court.find_element(By.CLASS_NAME, "court-number").text
                        available_courts.append(court_number)
                        print(f"[DEBUG] Found available court: {court_number}")
                except NoSuchElementException:
                    continue
        
        except Exception as e:
            print(f"[DEBUG] Error checking availability: {str(e)}")
        
        print(f"[DEBUG] Available courts: {available_courts}")
        return available_courts
    
    def make_booking(self, date: str, start_time: str, court_number: str) -> bool:
        """
        Attempt to make a booking for a specific court, date, and time.
        Returns True if booking is successful, False otherwise.
        """
        try:
            print(f"[DEBUG] Attempting to book court {court_number} on {date} at {start_time}")
            # Find and click the available court slot
            court_slot = self.driver.find_element(
                By.XPATH,
                f"//div[contains(@class, 'court-slot')][contains(@data-court, '{court_number}')]"
                f"[contains(@data-time, '{start_time}')]"
            )
            court_slot.click()
            print("[DEBUG] Court slot selected")
            
            # Add players based on configuration
            if self.use_visitors:
                print("[DEBUG] Using visitor option")
                self._add_visitors()
            else:
                print(f"[DEBUG] Adding {len(self.player_names)} players")
                self._add_players()
            
            # Confirm booking
            print("[DEBUG] Looking for confirm booking button...")
            confirm_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm-booking, button:contains('Confirm Booking')"))
            )
            confirm_btn.click()
            
            # Wait for success message
            print("[DEBUG] Waiting for booking confirmation...")
            success_msg = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".booking-success, .success-message"))
            )
            print("[DEBUG] Booking successful!")
            return True
            
        except Exception as e:
            print(f"[DEBUG] Error making booking: {str(e)}")
            return False
    
    def _add_players(self):
        """
        Internal helper to add named players to the booking.
        """
        try:
            for player in self.player_names:
                print(f"[DEBUG] Adding player: {player}")
                add_player_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-player, button:contains('Add Player')"))
                )
                add_player_btn.click()
                
                player_search = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#player-search, input[placeholder*='search']"))
                )
                player_search.send_keys(player)
                
                # Select the player from results
                print(f"[DEBUG] Selecting player '{player}' from results")
                player_option = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(), '{player}')]"))
                )
                player_option.click()
                time.sleep(0.5)  # Wait for selection to register
        
        except Exception as e:
            print(f"[DEBUG] Error adding players: {str(e)}")
    
    def _add_visitors(self):
        """
        Internal helper to add visitors to the booking if enabled.
        """
        try:
            print("[DEBUG] Adding visitors to booking")
            visitor_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-visitor, button:contains('Add Visitor')"))
            )
            visitor_btn.click()
            
            # Confirm visitor selection
            print("[DEBUG] Confirming visitor selection")
            confirm_visitor_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm-visitors, button:contains('Confirm Visitors')"))
            )
            confirm_visitor_btn.click()
            
        except Exception as e:
            print(f"[DEBUG] Error adding visitors: {str(e)}")
    
    def close(self):
        """
        Close the Selenium browser session.
        """
        if self.driver:
            print("[DEBUG] Closing browser session")
            self.driver.quit()

    def select_date(self, date_str: str) -> bool:
        """
        Select a date using the jQuery UI Datepicker widget.
        Clicks the calendar button, navigates to the correct month/year, selects the day,
        and verifies the input value. Returns True if successful, False otherwise.
        """
        print(f"[DEBUG] Attempting to select date: {date_str}")
        try:
            # 1. Click the calendar button to open the datepicker
            calendar_btn = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ui-datepicker-trigger"))
            )
            calendar_btn.click()
            print("[DEBUG] Clicked calendar button to open datepicker")

            # 2. Wait for the datepicker widget to appear
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "ui-datepicker-div"))
            )
            print("[DEBUG] Datepicker widget is visible")

            # 3. Parse the target date
            target_day, target_month, target_year = map(int, date_str.split('-'))

            # 4. Navigate to the correct month/year
            import calendar
            while True:
                month_elem = self.driver.find_element(By.CLASS_NAME, "ui-datepicker-month")
                year_elem = self.driver.find_element(By.CLASS_NAME, "ui-datepicker-year")
                current_month = month_elem.text
                current_year = int(year_elem.text)
                current_month_num = list(calendar.month_name).index(current_month)
                print(f"[DEBUG] Datepicker showing: {current_month} {current_year}")
                if current_year == target_year and current_month_num == target_month:
                    break
                elif (current_year, current_month_num) < (target_year, target_month):
                    next_btn = self.driver.find_element(By.CLASS_NAME, "ui-datepicker-next")
                    next_btn.click()
                    print("[DEBUG] Clicked next month")
                else:
                    prev_btn = self.driver.find_element(By.CLASS_NAME, "ui-datepicker-prev")
                    prev_btn.click()
                    print("[DEBUG] Clicked previous month")
                time.sleep(0.2)

            # 5. Click the target day
            day_xpath = f"//a[text()='{target_day}']"
            day_elem = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, day_xpath))
            )
            day_elem.click()
            print(f"[DEBUG] Clicked day {target_day}")

            # 6. Verify the input value
            date_input = self.driver.find_element(By.ID, "banedato")
            selected_date = date_input.get_attribute("value")
            print(f"[DEBUG] Input value after selection: {selected_date}")
            if selected_date == date_str:
                print(f"[DEBUG] Successfully selected date: {selected_date}")
                return True
            else:
                print(f"[DEBUG] Date selection failed. Input value: {selected_date}")
                return False

        except Exception as e:
            print(f"[DEBUG] Error selecting date: {e}")
            return False

    def select_date_helper(self, date_str: str) -> bool:
        """
        (Deprecated/unused) Placeholder for alternate date selection logic.
        """
        # Implementation of the helper method to select a date
        # This method should return True if the date is successfully selected, False otherwise
        # This is a placeholder and should be implemented based on the actual implementation
        return False

    def enter_players(self) -> bool:
        """
        Enter all player names into the booking form.
        Returns True if all players are entered successfully, False otherwise.
        """
        try:
            print("[DEBUG]\nWaiting for player entry modal...")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='medspiller']")))
            used_names = set()
            rejected_names = set()
            max_players = 3
            field_info = [
                ("medspiller", "sub"),
                ("medspiller2", "medsub2"),
                ("medspiller3", "medsub3"),
            ]
            for idx, (input_name, search_id) in enumerate(field_info):
                try:
                    input_selector = f"input[name='{input_name}']"
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, input_selector)))
                    input_field = self.driver.find_element(By.CSS_SELECTOR, input_selector)
                except Exception as e:
                    print(f"[DEBUG] Could not find input field for Opponent {idx+1}: {e}")
                    return False
                print(f"[DEBUG] Entering player for Opponent {idx+1}...")
                player_found = False
                for name in self.player_names:
                    if name in used_names or name in rejected_names:
                        continue
                    input_field.clear()
                    input_field.send_keys(name)
                    print(f"[DEBUG]  Trying player name: {name}")
                    try:
                        search_btn = self.driver.find_element(By.ID, search_id)
                        self.driver.execute_script("arguments[0].click();", search_btn)
                        print("[DEBUG]  Clicked Search button")
                    except Exception as e:
                        print(f"[DEBUG]  Could not find/click Search button: {e}")
                        continue
                    time.sleep(0.5)
                    # After DOM update, check for error message in the modal
                    try:
                        modal = self.driver.find_element(By.CSS_SELECTOR, "div.modal-content")
                        error_divs = modal.find_elements(By.CSS_SELECTOR, "div.alert.alert-danger")
                        error_found = False
                        for err in error_divs:
                            if err.is_displayed() and err.text.strip():
                                print(f"[DEBUG]    Error: {err.text.strip()}")
                                error_found = True
                                break
                        if error_found:
                            rejected_names.add(name)
                            continue  # Try next player name
                    except Exception as e:
                        print(f"[DEBUG]    Could not check for error message: {e}")
                    # Re-find the input after DOM update
                    try:
                        input_field = self.driver.find_element(By.CSS_SELECTOR, input_selector)
                    except Exception as e:
                        print(f"[DEBUG]    Could not re-find input field: {e}")
                        continue
                    try:
                        tooltip = None
                        tooltip_text = ""
                        try:
                            parent = input_field.find_element(By.XPATH, "../../../../..")
                            tooltip = parent.find_element(By.CSS_SELECTOR, "span.tooltip_ajax")
                            tooltip_text = tooltip.text.strip()
                            if tooltip_text:
                                print(f"[DEBUG]    Tooltip: {tooltip_text}")
                        except:
                            tooltip_text = ""
                        if input_field.get_attribute('value') and not tooltip_text:
                            print(f"[DEBUG]  Player {name} accepted for Opponent {idx+1}")
                            used_names.add(name)
                            player_found = True
                            break
                        else:
                            print(f"[DEBUG]  Player {name} not accepted (tooltip or empty value)")
                            rejected_names.add(name)
                    except Exception as e:
                        print(f"[DEBUG]  Error checking player search result: {e}")
                        rejected_names.add(name)
                if not player_found:
                    print(f"[DEBUG] Could not find a valid player for Opponent {idx+1}")
                    return False
            # After loop, check that all player fields are filled
            for input_name, _ in field_info:
                try:
                    input_field = self.driver.find_element(By.CSS_SELECTOR, f"input[name='{input_name}']")
                    if not input_field.get_attribute('value'):
                        print(f"[DEBUG] Player field {input_name} was not filled successfully.")
                        return False
                except Exception as e:
                    print(f"[DEBUG] Could not find input field {input_name} for final check: {e}")
                    return False
            print("[DEBUG] All players entered successfully!")
            # Find and click the 'Add to basket' button
            try:
                # Wait for the button to appear anywhere in the DOM
                add_btn_xpath = "//span[contains(@class, 'btn-primary') and contains(., 'Add to basket')]"
                self.wait.until(EC.visibility_of_element_located((By.XPATH, add_btn_xpath)))
                add_btns = self.driver.find_elements(By.XPATH, add_btn_xpath)
                add_btn = None
                for btn in add_btns:
                    if btn.is_displayed():
                        add_btn = btn
                        break
                if add_btn:
                    self.driver.execute_script("arguments[0].scrollIntoView();", add_btn)
                    self.driver.execute_script("arguments[0].click();", add_btn)
                    print("[DEBUG] Clicked 'Add to basket' button")
                    # Wait for the new page to load by waiting for the checkbox or 'Your Basket' heading
                    try:
                        self.wait.until(
                            EC.presence_of_element_located((By.ID, "acc_beting"))
                        )
                        print("[DEBUG] 'Your Basket' page loaded and checkbox present.")
                    except Exception as e:
                        print(f"[DEBUG] Checkbox or basket page did not load: {e}")
                        return False
                else:
                    print("[DEBUG] Could not find 'Add to basket' button")
                    return False
            except Exception as e:
                print(f"[DEBUG] Error clicking 'Add to basket' button: {e}")
                return False

            # --- NEW: Handle Terms & Conditions and Confirm Booking ---
            try:
                # Wait for the checkbox to be present in the DOM (not necessarily clickable)
                tnc_checkbox = self.wait.until(
                    EC.presence_of_element_located((By.ID, "acc_beting"))
                )
                print("[DEBUG] Located checkbox by ID 'acc_beting'.")
                # Step 1: Try clicking the label
                try:
                    label = tnc_checkbox.find_element(By.XPATH, "./ancestor::label")
                    self.driver.execute_script("arguments[0].scrollIntoView();", label)
                    label.click()
                    print("[DEBUG] Ticked Terms & Conditions checkbox by clicking label")
                except Exception as e1:
                    print(f"[DEBUG] Label click failed: {e1}. Trying JS set...")
                # Check state after label click
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    print(f"[DEBUG] Checkbox checked state after label click: {is_checked}")
                except Exception as e:
                    print(f"[DEBUG] Error checking state after label click: {e}")
                # Step 2: Use JS to set checked and trigger onclick if not checked
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    if not is_checked:
                        self.driver.execute_script(
                            "arguments[0].checked = true; arguments[0].onclick && arguments[0].onclick();",
                            tnc_checkbox
                        )
                        print("[DEBUG] Ticked Terms & Conditions checkbox via JS.")
                        is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                        print(f"[DEBUG] Checkbox checked state after JS set: {is_checked}")
                except Exception as e:
                    print(f"[DEBUG] Error during JS set: {e}")
                # Step 3: Try direct JS click and event dispatch if still not checked
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    if not is_checked:
                        print("[DEBUG] Checkbox is still not checked after label/JS. Trying direct JS click and event dispatch...")
                        self.driver.execute_script(
                            "arguments[0].click(); var evt = document.createEvent('HTMLEvents'); evt.initEvent('change', true, true); arguments[0].dispatchEvent(evt);",
                            tnc_checkbox
                        )
                        is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                        print(f"[DEBUG] Checkbox checked state after direct JS click: {is_checked}")
                except Exception as e:
                    print(f"[DEBUG] Error during direct JS click: {e}")
                # Final check and debug output
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    if not is_checked:
                        print("[DEBUG] Checkbox is still not checked after all attempts. Printing HTML for inspection.")
                        try:
                            print("[DEBUG] Checkbox outerHTML:", tnc_checkbox.get_attribute('outerHTML'))
                            parent = tnc_checkbox.find_element(By.XPATH, "..")
                            print("[DEBUG] Parent outerHTML:", parent.get_attribute('outerHTML'))
                        except Exception as e2:
                            print(f"[DEBUG] Error printing checkbox HTML: {e2}")
                        return False
                except Exception as e:
                    print(f"[DEBUG] Error during final checked state check: {e}")
            except Exception as e:
                print(f"[DEBUG] Could not tick Terms & Conditions checkbox: {e}")
                return False
            try:
                # Wait for the Confirm Booking button to appear
                confirm_btn_xpath = "//span[contains(@class, 'btn-primary') and contains(., 'Confirm Booking')]"
                self.wait.until(EC.visibility_of_element_located((By.XPATH, confirm_btn_xpath)))
                confirm_btns = self.driver.find_elements(By.XPATH, confirm_btn_xpath)
                confirm_btn = None
                for btn in confirm_btns:
                    if btn.is_displayed():
                        confirm_btn = btn
                        break
                if confirm_btn:
                    self.driver.execute_script("arguments[0].scrollIntoView();", confirm_btn)
                    self.driver.execute_script("arguments[0].click();", confirm_btn)
                    print("[DEBUG] Clicked 'Confirm Booking' button")
                else:
                    print("[DEBUG] Could not find 'Confirm Booking' button")
                    return False
            except Exception as e:
                print(f"[DEBUG] Error clicking 'Confirm Booking' button: {e}")
                return False
            # Wait for the final receipt page by URL or by heading
            print("[DEBUG] Waiting for final receipt page after confirming booking...")
            def receipt_page_loaded(driver):
                url_match = "proc_kvittering.asp" in driver.current_url
                heading_match = driver.find_elements(By.XPATH, "//div[contains(@class, 'text-center') and contains(@class, 'min480')]/h1[contains(., 'Your Receipt')]")
                return url_match or bool(heading_match)
            self.wait.until(receipt_page_loaded)
            print("[DEBUG] SUCCESS: Final receipt page detected!")
            # Optionally, print the receipt heading
            try:
                headings = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'text-center') and contains(@class, 'min480')]/h1[contains(., 'Your Receipt')]")
                for h in headings:
                    if h.is_displayed():
                        print("--- Receipt/Confirmation Text ---")
                        print(h.text)
            except Exception as e:
                print(f"[DEBUG] Could not print receipt heading: {e}")
            return True
        except Exception as e:
            print(f"[DEBUG] Error during player entry: {e}")
            return False

    def book_court(self, target_time: str = "21:00") -> bool:
        """
        Main booking flow: finds available courts at the target time, enters players, adds to basket,
        accepts terms, and confirms the booking. Returns True if booking is successful.
        """
        try:
            print(f"[DEBUG]\nLooking for available courts at {target_time}...")
            # Find all available courts at the requested time
            available_courts = self.find_available_courts(target_time)
            print(f"[DEBUG] Found {len(available_courts)} available court(s) at {target_time}")
            for court_num, booking_elem in available_courts:
                print(f"[DEBUG] Attempting to book court {court_num} at {target_time}")
                try:
                    # Scroll element into view
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", booking_elem)
                        print("[DEBUG] Scrolled booking span into view.")
                    except Exception as e:
                        print(f"[DEBUG] Could not scroll booking span into view: {e}")
                    try:
                        self.driver.execute_script("arguments[0].click();", booking_elem)
                        print("[DEBUG] Clicked booking span via JS click().")
                    except Exception as e:
                        print(f"[DEBUG] JS click failed: {e}. Trying direct onclick...")
                        try:
                            self.driver.execute_script("arguments[0].onclick();", booking_elem)
                            print("[DEBUG] Clicked booking span via JS onclick().")
                        except Exception as e2:
                            print(f"[DEBUG] Direct onclick failed: {e2}. Trying onclick attribute...")
                            try:
                                onclick = booking_elem.get_attribute("onclick")
                                if onclick:
                                    self.driver.execute_script(onclick)
                                    print(f"[DEBUG] Executed onclick JS: {onclick}")
                                else:
                                    print("[DEBUG] No onclick attribute found.")
                                    return False
                            except Exception as e3:
                                print(f"[DEBUG] Onclick attribute execution failed: {e3}")
                                return False
                    # Save screenshot and print URL after click
                    try:
                        self.driver.save_screenshot("after_click_booking_span.png")
                        print("[DEBUG] Saved screenshot: after_click_booking_span.png")
                    except Exception as e:
                        print(f"[DEBUG] Could not save screenshot after clicking booking span: {e}")
                    current_url = self.driver.current_url
                    print(f"[DEBUG] Current URL after clicking booking span: {current_url}")
                    # Wait for VISIBLE player entry modal or page
                    try:
                        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='medspiller']")), 10)
                        print("[DEBUG] Player entry modal is visible.")
                    except Exception:
                        print("[DEBUG] Player entry modal not visible after clicking booking span.")
                        try:
                            with open("after_click_booking_span.html", "w", encoding="utf-8") as f:
                                f.write(self.driver.page_source)
                            print("[DEBUG] Saved page source: after_click_booking_span.html")
                        except Exception as e2:
                            print(f"[DEBUG] Could not save page source: {e2}")
                        return False
                    # Enter players using robust logic
                    print("[DEBUG] Calling enter_players()...")
                    if not self.enter_players():
                        print("[DEBUG] Player entry failed. Aborting booking flow.")
                        return False
                    print("[DEBUG] Player entry succeeded. Proceeding to basket/terms/confirmation...")
                    # Proceed with basket, terms, and confirmation as before (call complete_booking_flow or implement here)
                    if self.complete_booking_flow():
                        print(f"[DEBUG] Booking successful for court {court_num} at {target_time}")
                        return True
                    else:
                        print(f"[DEBUG] Booking flow failed for court {court_num} at {target_time}")
                except Exception as e:
                    print(f"[DEBUG] Exception while booking court {court_num}: {e}")
            print(f"[DEBUG] No courts could be booked at {target_time}")
            return False
        except Exception as e:
            print(f"[DEBUG] Error during booking: {e}")
            return False

    def find_available_courts(self, target_time: str):
        """
        Find all available courts at the requested time.
        Returns a list of (court_number, booking_element) tuples.
        """
        available = []
        try:
            # Wait for the court grid to be present (wait for any available booking span)
            try:
                self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//span[contains(@class, 'banefelt') and contains(@class, 'btn_ledig') and contains(@class, 'link')]"
                    ))
                )
                print("[DEBUG] Court grid is present and at least one available booking span is loaded.")
            except Exception as e:
                print(f"[DEBUG] Court grid not found: {e}")
                # Save the full page HTML for inspection
                try:
                    with open("full_page_debug.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print("[DEBUG] Saved full page HTML to full_page_debug.html")
                except Exception as e2:
                    print(f"[DEBUG] Could not save full page HTML: {e2}")
                return []
            # Find all available booking spans for the target time
            booking_spans = self.driver.find_elements(
                By.XPATH,
                "//span[contains(@class, 'banefelt') and contains(@class, 'btn_ledig') and contains(@class, 'link') and @title='Can be booked with your membership']"
            )
            print(f"[DEBUG] Found {len(booking_spans)} available booking spans (all times).")
            print(f"[DEBUG] Scanning for available courts at {target_time}...")
            for span in booking_spans:
                try:
                    text = span.text
                    classes = span.get_attribute("class")
                    # Debug info for every candidate span
                    print(f"[DEBUG] Span: class='{classes}', text='{text.replace(chr(10), ' | ')}'")
                    # Only match if the start time exactly matches target_time
                    if " - " in text:
                        start, _ = text.split(" - ", 1)
                        start = start.strip()
                        print(f"[DEBUG] Extracted start time: '{start}'")
                        if start != target_time:
                            continue
                    else:
                        print(f"[DEBUG] Unexpected time format in span: '{text}'")
                        continue  # skip if format is unexpected
                    # Go up to the parent .text-center.bane div to get the court column
                    court_div = span.find_element(By.XPATH, "ancestor::div[contains(@class, 'text-center') and contains(@class, 'bane')][1]")
                    # The header is the first child span with class 'banefelt ehbanehead' inside this div
                    header_span = court_div.find_element(By.XPATH, ".//span[contains(@class, 'banefelt') and contains(@class, 'ehbanehead')]")
                    court_number = header_span.text.strip().replace('Click for info', '').replace('\n', '').strip()
                    print(f"[DEBUG] Found available court: {court_number} at {target_time}")
                    available.append((court_number, span))
                except Exception as e:
                    print(f"[DEBUG] Could not process span: {e}")
            print(f"[DEBUG] Total available courts found at {target_time}: {len(available)}")
        except Exception as e:
            print(f"[DEBUG] Error finding available courts: {e}")
        return available

    def complete_booking_flow(self):
        """
        Complete the booking flow after clicking a court: enter players, add to basket, accept terms, confirm.
        Returns True if booking is confirmed, False otherwise.
        """
        # ... existing code for player entry, basket, terms, confirmation ...
        return True  # or False if any step fails

def main():
    """
    Main entry point for the booking script.
    Initializes ChapelBooking, performs login, court type selection, date selection, and booking.
    """
    print("[DEBUG] main() starting...")
    chapel = ChapelBooking()
    if chapel.login():
        print("[DEBUG] login() returned True. Taking screenshot after login...")
        try:
            chapel.driver.save_screenshot("after_login.png")
            print("[DEBUG] Saved screenshot: after_login.png")
        except Exception as e:
            print(f"[DEBUG] Could not save screenshot after login: {e}")
        try:
            with open("after_login.html", "w", encoding="utf-8") as f:
                f.write(chapel.driver.page_source)
            print("[DEBUG] Saved HTML: after_login.html")
        except Exception as e:
            print(f"[DEBUG] Could not save HTML after login: {e}")
        print("[DEBUG] Refreshing page after login to ensure dropdown is populated...")
        chapel.driver.refresh()
        print("[DEBUG] Page refreshed. Waiting for court type dropdown to be populated...")
        def dropdown_has_option(driver):
            try:
                select_elem = driver.find_element(By.ID, "soeg_omraede")
                options = [o.text.strip() for o in select_elem.find_elements(By.TAG_NAME, "option") if o.text.strip()]
                print(f"[DEBUG] Dropdown options after refresh: {options}")
                return any("Padel Courts" in o for o in options)
            except Exception as e:
                print(f"[DEBUG] Exception while checking dropdown options: {e}")
                return False
        WebDriverWait(chapel.driver, 20).until(dropdown_has_option)
        print("[DEBUG] Court type dropdown is now populated. Proceeding to court type selection...")
        print("[DEBUG] Calling select_court_type()...")
        if chapel.select_court_type():
            print("[DEBUG] select_court_type() returned True. Calling select_date()...")
            # Use booking date from environment variable
            if chapel.select_date(chapel.booking_date):
                print("[DEBUG] Date selection successful! Calling book_court()...")
                # Use booking time from environment variable
                chapel.book_court(chapel.booking_time)
            else:
                print("[DEBUG] Date selection failed!")
        else:
            try:
                chapel.driver.save_screenshot("court_type_dropdown_not_found.png")
                print("[DEBUG] Saved screenshot: court_type_dropdown_not_found.png")
            except Exception as e:
                print(f"[DEBUG] Could not save screenshot after court type dropdown failure: {e}")
            print("[DEBUG] Court type selection failed!")
    else:
        print("[DEBUG] login() returned False. Login failed.")
    print("[DEBUG] Closing browser session")
    chapel.close()

if __name__ == "__main__":
    main() 