import os
import time
import base64
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urlparse, urlunparse

class ChapelBooking:
    BASE_URL = "https://chapel-a.clubsolution.co.uk/newlook/proc_baner.asp"
    
    def __init__(self):
        load_dotenv()
        self.username = os.getenv("CHAPEL_USERNAME")
        self.password = os.getenv("CHAPEL_PASSWORD")
        
        # Handle player names with potential spaces
        player_names = os.getenv("PLAYER_NAMES", "")
        self.player_names = [name.strip() for name in player_names.split(",") if name.strip()]
        print(f"Loaded {len(self.player_names)} player names")
        
        self.use_visitors = os.getenv("USE_VISITORS", "false").lower() == "true"
        self.court_type = os.getenv("DEFAULT_COURT_TYPE", "Padel Courts")
        
        if not self.username or not self.password:
            raise ValueError("Username and password must be set in .env file")
        
        # Initialize Chrome driver
        print("Initializing Chrome driver...")
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")
        
        # Set up Chrome preferences
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False
        })
        
        # Create driver
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)  # Increased timeout
        print("Chrome driver initialized successfully")
    
    def login(self) -> bool:
        """Log in to the website."""
        try:
            print("Navigating to website...")
            self.driver.get(self.BASE_URL)
            
            # Handle cookie consent first
            self.handle_cookie_consent()
            
            # Find and click the login link
            print("Looking for login link...")
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
                        print(f"Found login link with selector: {selector}")
                        break
                except:
                    continue
            
            if not login_link:
                print("Could not find login link")
                return False
            
            # Click the login link to open modal
            login_link.click()
            print("Clicked login link")
            
            # Wait for login modal to appear and be visible
            print("Waiting for login modal...")
            modal = self.wait.until(
                EC.visibility_of_element_located((By.ID, "loginModal"))
            )
            print("Login modal found")
            
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
                        print(f"Found username field with selector: {selector}")
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
                        print(f"Found password field with selector: {selector}")
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
            print("Entered credentials")

            # Optionally check the 'Stay Logged in' checkbox if present and not already checked
            try:
                stay_logged_in = modal.find_element(By.ID, "husklogin")
                if not stay_logged_in.is_selected():
                    stay_logged_in.click()
                    print("Checked 'Stay Logged in' checkbox")
                else:
                    print("'Stay Logged in' checkbox already checked")
            except Exception as e:
                print("'Stay Logged in' checkbox not found or could not be checked (optional)")

            # Send Enter key after entering password
            enter_sent = False
            try:
                password_field.send_keys(Keys.RETURN)
                print("Sent Enter key after password")
                enter_sent = True
            except Exception as e:
                print(f"Could not send Enter key: {e}")
                enter_sent = False

            # Only click the login button if Enter was not sent
            if not enter_sent:
                try:
                    login_button = modal.find_element(By.ID, "sub")
                    print("Found login button <span> with id='sub'")
                except Exception as e:
                    print(f"Could not find login button <span> with id='sub': {e}")
                    return False
                # Try clicking the button using JavaScript (to trigger the onclick handler)
                try:
                    self.driver.execute_script("arguments[0].click();", login_button)
                    print("Clicked login button using JavaScript")
                except Exception as e:
                    print(f"JavaScript click failed: {e}, trying normal click...")
                    try:
                        login_button.click()
                        print("Clicked login button using Selenium click")
                    except Exception as e2:
                        print(f"Both click methods failed: {e2}")
                        return False
                print("Submitted login form")
            else:
                print("Submitted login form via Enter key")
            
            # Print the modal HTML after login attempt for debugging
            try:
                modal_html = modal.get_attribute('outerHTML')
                print("\nLogin modal HTML after login attempt:")
                print(modal_html)
            except Exception as e:
                print(f"Could not get modal HTML: {e}")
            
            # Wait for login modal to disappear
            try:
                print("Waiting for login modal to disappear...")
                self.wait.until(EC.invisibility_of_element_located((By.ID, "loginModal")))
                print("Login modal disappeared")
            except Exception as e:
                print(f"Login modal did not disappear: {e}")

            # Wait for the generic username span to appear (indicating successful login for any user)
            try:
                print("Waiting for username to appear in top right (any user)...")
                user_xpath = "//span[i[contains(@class, 'fa-user')]]/span[contains(@class, 'caret')]/.."
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, user_xpath))
                )
                user_span = self.driver.find_element(By.XPATH, user_xpath)
                username = user_span.text.replace('caret', '').strip()
                print(f"Login successful - username found in top right: {username}")
                return True
            except TimeoutException:
                print("Timeout waiting for username to appear - login may have failed")
                return False
            
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False
    
    def handle_cookie_consent(self) -> bool:
        """Handle cookie consent popup if present."""
        try:
            # Only check for cookie consent once per session
            if hasattr(self, '_cookie_consent_handled'):
                return True
                
            print("Checking for cookie consent popup...")
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
                    print("Clicked cookie consent button")
                    self._cookie_consent_handled = True
                    return True
                except:
                    continue
            
            # If we get here, either there was no cookie popup or we couldn't handle it
            self._cookie_consent_handled = True
            return True
            
        except Exception as e:
            print(f"Error handling cookie consent: {str(e)}")
            return False

    def select_court_type(self) -> bool:
        """Select the court type (e.g., Padel Courts)."""
        try:
            print(f"Attempting to select court type: {self.court_type}")
            
            # Quick check for cookie consent
            if not self.handle_cookie_consent():
                print("Failed to handle cookie consent")
                return False

            # Wait for the court type dropdown to be present
            print("Waiting for court type dropdown...")
            try:
                # First find the dropdown button that shows the current selection
                dropdown_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.dropdown-toggle[data-toggle='dropdown']"))
                )
                print("Found court type dropdown button")
                
                # Get the current selection
                current_selection = dropdown_button.find_element(By.CSS_SELECTOR, "span.filter-option.pull-left").text
                print(f"Current selection: {current_selection}")
                
                # If already selected, no need to change
                if current_selection == self.court_type:
                    print("Correct court type already selected")
                    return True
                
                # Click the dropdown to open it
                dropdown_button.click()
                print("Clicked dropdown button")
                
                # Wait for dropdown menu to appear and find the correct option
                dropdown_menu = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.dropdown-menu"))
                )
                
                # Find the specific court type option
                court_option = dropdown_menu.find_element(
                    By.XPATH, f"//span[contains(text(), '{self.court_type}')]"
                )
                print(f"Found {self.court_type} option")
                
                # Click the option
                court_option.click()
                print(f"Selected {self.court_type}")
                
                # Wait for the page to update
                time.sleep(1)
                return True
                
            except TimeoutException:
                print("Timeout waiting for court type dropdown")
                return False
            except NoSuchElementException:
                print(f"Could not find {self.court_type} option in dropdown")
                return False
            
        except Exception as e:
            print(f"Error selecting court type: {str(e)}")
            return False
    
    def check_availability(self, date: str, start_time: str, end_time: str) -> List[str]:
        """
        Check court availability for a specific date and time range.
        
        Args:
            date: Date in format 'YYYY-MM-DD'
            start_time: Start time in format 'HH:MM'
            end_time: End time in format 'HH:MM'
            
        Returns:
            List of available court numbers
        """
        available_courts = []
        
        try:
            print(f"Checking availability for date: {date}, time: {start_time}-{end_time}")
            # Navigate to the date
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d-%m-%Y")
            
            # TODO: Implement date navigation
            print("Looking for available courts...")
            # Check each court's availability
            courts = self.driver.find_elements(By.CLASS_NAME, "court-slot")
            print(f"Found {len(courts)} court slots")
            
            for court in courts:
                try:
                    time_slot = court.find_element(By.CLASS_NAME, "time-slot")
                    if start_time in time_slot.text and "available" in court.get_attribute("class"):
                        court_number = court.find_element(By.CLASS_NAME, "court-number").text
                        available_courts.append(court_number)
                        print(f"Found available court: {court_number}")
                except NoSuchElementException:
                    continue
        
        except Exception as e:
            print(f"Error checking availability: {str(e)}")
        
        print(f"Available courts: {available_courts}")
        return available_courts
    
    def make_booking(self, date: str, start_time: str, court_number: str) -> bool:
        """
        Make a booking for a specific court.
        
        Args:
            date: Date in format 'YYYY-MM-DD'
            start_time: Start time in format 'HH:MM'
            court_number: Court number to book
            
        Returns:
            Boolean indicating if booking was successful
        """
        try:
            print(f"Attempting to book court {court_number} on {date} at {start_time}")
            # Find and click the available court slot
            court_slot = self.driver.find_element(
                By.XPATH,
                f"//div[contains(@class, 'court-slot')][contains(@data-court, '{court_number}')]"
                f"[contains(@data-time, '{start_time}')]"
            )
            court_slot.click()
            print("Court slot selected")
            
            # Add players based on configuration
            if self.use_visitors:
                print("Using visitor option")
                self._add_visitors()
            else:
                print(f"Adding {len(self.player_names)} players")
                self._add_players()
            
            # Confirm booking
            print("Looking for confirm booking button...")
            confirm_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm-booking, button:contains('Confirm Booking')"))
            )
            confirm_btn.click()
            
            # Wait for success message
            print("Waiting for booking confirmation...")
            success_msg = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".booking-success, .success-message"))
            )
            print("Booking successful!")
            return True
            
        except Exception as e:
            print(f"Error making booking: {str(e)}")
            return False
    
    def _add_players(self):
        """Add predefined players to the booking."""
        try:
            for player in self.player_names:
                print(f"Adding player: {player}")
                add_player_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-player, button:contains('Add Player')"))
                )
                add_player_btn.click()
                
                player_search = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#player-search, input[placeholder*='search']"))
                )
                player_search.send_keys(player)
                
                # Select the player from results
                print(f"Selecting player '{player}' from results")
                player_option = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(), '{player}')]"))
                )
                player_option.click()
                time.sleep(0.5)  # Wait for selection to register
        
        except Exception as e:
            print(f"Error adding players: {str(e)}")
    
    def _add_visitors(self):
        """Add visitors to the booking."""
        try:
            print("Adding visitors to booking")
            visitor_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-visitor, button:contains('Add Visitor')"))
            )
            visitor_btn.click()
            
            # Confirm visitor selection
            print("Confirming visitor selection")
            confirm_visitor_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm-visitors, button:contains('Confirm Visitors')"))
            )
            confirm_visitor_btn.click()
            
        except Exception as e:
            print(f"Error adding visitors: {str(e)}")
    
    def close(self):
        """Close the browser session."""
        if self.driver:
            print("Closing browser session")
            self.driver.quit()

    def select_date(self, target_date: str) -> bool:
        """Select a date in the calendar.
        
        Args:
            target_date: Date in DD-MM-YYYY format
        """
        try:
            print(f"\nAttempting to select date: {target_date}")
            
            # Find the date input field
            date_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "banedato"))
            )
            print("Found date input field")
            
            # Get current selected date before clicking
            current_date = date_input.get_attribute('value')
            print(f"Current date: {current_date}")
            
            # Parse dates
            target_day, target_month, target_year = map(int, target_date.split('-'))
            current_day, current_month, current_year = map(int, current_date.split('-'))
            
            # If already on correct date, no need to change
            if current_date == target_date:
                print("Already on correct date")
                return True
            
            # Click to open the datepicker
            date_input.click()
            print("Clicked date input to open datepicker")
            
            # Wait for datepicker to be visible
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-datepicker-calendar"))
            )
            
            # Calculate how many months to move forward/backward
            months_diff = (target_year - current_year) * 12 + (target_month - current_month)
            
            if months_diff != 0:
                # Find month navigation buttons
                if months_diff > 0:
                    print(f"Moving forward {months_diff} months")
                    for _ in range(months_diff):
                        next_button = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-datepicker-next"))
                        )
                        next_button.click()
                        time.sleep(0.2)  # Small delay between clicks
                else:
                    print(f"Moving backward {abs(months_diff)} months")
                    for _ in range(abs(months_diff)):
                        prev_button = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-datepicker-prev"))
                        )
                        prev_button.click()
                        time.sleep(0.2)
            
            # Wait for the calendar to update
            time.sleep(0.5)
            
            # Find and click the target day
            day_selectors = [
                f"//a[text()='{target_day}']",
                f"//td[@data-handler='selectDay']/a[text()='{target_day}']",
                f"//td[not(contains(@class, 'ui-datepicker-other-month'))]/a[text()='{target_day}']"
            ]
            
            day_element = None
            for selector in day_selectors:
                try:
                    day_element = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if day_element:
                        break
                except:
                    continue
            
            if not day_element:
                print(f"Could not find day {target_day}")
                return False
            
            # Click the day
            day_element.click()
            print(f"Clicked day {target_day}")
            
            # Wait for the date to be updated and verify
            time.sleep(0.5)  # Wait for any animations/updates
            
            # Get fresh reference to input
            date_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "banedato"))
            )
            selected_date = date_input.get_attribute('value')
            
            if selected_date == target_date:
                print(f"Successfully selected date: {selected_date}")
                return True
            else:
                print(f"Date selection failed. Current value: {selected_date}")
                return False
            
        except Exception as e:
            print(f"Error selecting date: {str(e)}")
            return False

    def enter_players(self) -> bool:
        """Enter player names in the booking modal using the provided player list, handling errors and ensuring all fields are filled. Never retry a rejected player for any slot."""
        try:
            print("\nWaiting for player entry modal...")
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
                    print(f"Could not find input field for Opponent {idx+1}: {e}")
                    return False
                print(f"Entering player for Opponent {idx+1}...")
                player_found = False
                for name in self.player_names:
                    if name in used_names or name in rejected_names:
                        continue
                    input_field.clear()
                    input_field.send_keys(name)
                    print(f"  Trying player name: {name}")
                    try:
                        search_btn = self.driver.find_element(By.ID, search_id)
                        self.driver.execute_script("arguments[0].click();", search_btn)
                        print("  Clicked Search button")
                    except Exception as e:
                        print(f"  Could not find/click Search button: {e}")
                        continue
                    time.sleep(0.5)
                    # After DOM update, check for error message in the modal
                    try:
                        modal = self.driver.find_element(By.CSS_SELECTOR, "div.modal-content")
                        error_divs = modal.find_elements(By.CSS_SELECTOR, "div.alert.alert-danger")
                        error_found = False
                        for err in error_divs:
                            if err.is_displayed() and err.text.strip():
                                print(f"    Error: {err.text.strip()}")
                                error_found = True
                                break
                        if error_found:
                            rejected_names.add(name)
                            continue  # Try next player name
                    except Exception as e:
                        print(f"    Could not check for error message: {e}")
                    # Re-find the input after DOM update
                    try:
                        input_field = self.driver.find_element(By.CSS_SELECTOR, input_selector)
                    except Exception as e:
                        print(f"    Could not re-find input field: {e}")
                        continue
                    try:
                        tooltip = None
                        tooltip_text = ""
                        try:
                            parent = input_field.find_element(By.XPATH, "../../../../..")
                            tooltip = parent.find_element(By.CSS_SELECTOR, "span.tooltip_ajax")
                            tooltip_text = tooltip.text.strip()
                            if tooltip_text:
                                print(f"    Tooltip: {tooltip_text}")
                        except:
                            tooltip_text = ""
                        if input_field.get_attribute('value') and not tooltip_text:
                            print(f"  Player {name} accepted for Opponent {idx+1}")
                            used_names.add(name)
                            player_found = True
                            break
                        else:
                            print(f"  Player {name} not accepted (tooltip or empty value)")
                            rejected_names.add(name)
                    except Exception as e:
                        print(f"  Error checking player search result: {e}")
                        rejected_names.add(name)
                if not player_found:
                    print(f"Could not find a valid player for Opponent {idx+1}")
                    return False
            # After loop, check that all player fields are filled
            for input_name, _ in field_info:
                try:
                    input_field = self.driver.find_element(By.CSS_SELECTOR, f"input[name='{input_name}']")
                    if not input_field.get_attribute('value'):
                        print(f"Player field {input_name} was not filled successfully.")
                        return False
                except Exception as e:
                    print(f"Could not find input field {input_name} for final check: {e}")
                    return False
            print("All players entered successfully!")
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
                    print("Clicked 'Add to basket' button")
                    # Wait for the new page to load by waiting for the checkbox or 'Your Basket' heading
                    try:
                        self.wait.until(
                            EC.presence_of_element_located((By.ID, "acc_beting"))
                        )
                        print("'Your Basket' page loaded and checkbox present.")
                    except Exception as e:
                        print(f"Checkbox or basket page did not load: {e}")
                        return False
                else:
                    print("Could not find 'Add to basket' button")
                    return False
            except Exception as e:
                print(f"Error clicking 'Add to basket' button: {e}")
                return False

            # --- NEW: Handle Terms & Conditions and Confirm Booking ---
            try:
                # Wait for the checkbox to be present in the DOM (not necessarily clickable)
                tnc_checkbox = self.wait.until(
                    EC.presence_of_element_located((By.ID, "acc_beting"))
                )
                print("Located checkbox by ID 'acc_beting'.")
                # Step 1: Try clicking the label
                try:
                    label = tnc_checkbox.find_element(By.XPATH, "./ancestor::label")
                    self.driver.execute_script("arguments[0].scrollIntoView();", label)
                    label.click()
                    print("Ticked Terms & Conditions checkbox by clicking label")
                except Exception as e1:
                    print(f"Label click failed: {e1}. Trying JS set...")
                # Check state after label click
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    print(f"Checkbox checked state after label click: {is_checked}")
                except Exception as e:
                    print(f"Error checking state after label click: {e}")
                # Step 2: Use JS to set checked and trigger onclick if not checked
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    if not is_checked:
                        self.driver.execute_script(
                            "arguments[0].checked = true; arguments[0].onclick && arguments[0].onclick();",
                            tnc_checkbox
                        )
                        print("Ticked Terms & Conditions checkbox via JS.")
                        is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                        print(f"Checkbox checked state after JS set: {is_checked}")
                except Exception as e:
                    print(f"Error during JS set: {e}")
                # Step 3: Try direct JS click and event dispatch if still not checked
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    if not is_checked:
                        print("Checkbox is still not checked after label/JS. Trying direct JS click and event dispatch...")
                        self.driver.execute_script(
                            "arguments[0].click(); var evt = document.createEvent('HTMLEvents'); evt.initEvent('change', true, true); arguments[0].dispatchEvent(evt);",
                            tnc_checkbox
                        )
                        is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                        print(f"Checkbox checked state after direct JS click: {is_checked}")
                except Exception as e:
                    print(f"Error during direct JS click: {e}")
                # Final check and debug output
                try:
                    is_checked = self.driver.execute_script("return arguments[0].checked;", tnc_checkbox)
                    if not is_checked:
                        print("Checkbox is still not checked after all attempts. Printing HTML for inspection.")
                        try:
                            print("Checkbox outerHTML:", tnc_checkbox.get_attribute('outerHTML'))
                            parent = tnc_checkbox.find_element(By.XPATH, "..")
                            print("Parent outerHTML:", parent.get_attribute('outerHTML'))
                        except Exception as e2:
                            print(f"Error printing checkbox HTML: {e2}")
                        return False
                except Exception as e:
                    print(f"Error during final checked state check: {e}")
            except Exception as e:
                print(f"Could not tick Terms & Conditions checkbox: {e}")
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
                    print("Clicked 'Confirm Booking' button")
                else:
                    print("Could not find 'Confirm Booking' button")
                    return False
            except Exception as e:
                print(f"Error clicking 'Confirm Booking' button: {e}")
                return False
            # Optionally, wait for a final booking confirmation message
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Booking confirmed') or contains(text(), 'bekræftet') or contains(text(), 'Reservation') or contains(text(), 'Tak for din booking') or contains(text(), 'Thank you for your booking') or contains(text(), 'Confirmed') or contains(text(), 'confirmed') or contains(text(), 'Reservation complete') or contains(text(), 'Reservation successful') or contains(text(), 'Bookingen er gennemført') or contains(text(), 'Bookingen er bekræftet') ]"))
                )
                print("Final booking confirmation detected!")
            except Exception as e:
                print(f"Final booking confirmation not detected: {e}")
            try:
                # Wait for the receipt page to load after confirming booking
                print("Waiting for receipt page after confirming booking...")
                # Try to detect a receipt heading or booking reference
                receipt_xpath = "//*[contains(text(), 'Receipt') or contains(text(), 'Booking reference') or contains(text(), 'Tak for din booking') or contains(text(), 'Thank you for your booking') or contains(text(), 'bekræftet') or contains(text(), 'Reservation') or contains(text(), 'Bookingen er gennemført') or contains(text(), 'Bookingen er bekræftet')]"
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, receipt_xpath))
                )
                print("SUCCESS: Booking completed and receipt page detected!")
                # Optionally, print the booking reference or receipt details
                try:
                    receipt_elements = self.driver.find_elements(By.XPATH, receipt_xpath)
                    for elem in receipt_elements:
                        if elem.is_displayed():
                            print("--- Receipt/Confirmation Text ---")
                            print(elem.text)
                except Exception as e:
                    print(f"Could not print receipt details: {e}")
            except Exception as e:
                print(f"WARNING: Receipt page or confirmation not detected: {e}")
            return True
        except Exception as e:
            print(f"Error during player entry: {e}")
            return False

    def book_court(self, target_time: str = "21:00") -> bool:
        """Attempt to book a court at the specified time (default 21:00)."""
        try:
            print(f"\nLooking for available courts at {target_time}...")
            # Wait for the booking elements to be present
            xpath = f"//span[contains(@class, 'banefelt') and contains(@class, 'btn_ledig') and contains(@class, 'link') and contains(., '{target_time}') and contains(., '- 22:00')]"
            self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            booking_spans = self.driver.find_elements(By.XPATH, xpath)
            if not booking_spans:
                print(f"No available courts at {target_time}")
                return False
            print(f"Found {len(booking_spans)} available court(s) at {target_time}")

            # Try to book the first available court
            btn = booking_spans[0]
            try:
                self.driver.execute_script("arguments[0].scrollIntoView();", btn)
                self.driver.execute_script("arguments[0].click();", btn)
                print("Clicked booking span for court")
            except Exception as e:
                print(f"Failed to click booking span: {e}")
                return False

            # Wait for player entry modal and enter players
            if not self.enter_players():
                print("Player entry failed or not all players could be entered.")
                return False

            # Wait for confirmation dialog or booking success indicator
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Booking confirmed') or contains(text(), 'bekræftet') or contains(text(), 'Reservation') or contains(text(), 'Tak for din booking') or contains(text(), 'Thank you for your booking')]"))
                )
                print("Booking confirmed!")
                return True
            except Exception as e:
                print(f"Booking may not have been confirmed: {e}")
                return False
        except Exception as e:
            print(f"Error during booking: {e}")
            return False

def main():
    chapel = ChapelBooking()
    try:
        if chapel.login():
            if chapel.select_court_type():
                # Test date selection
                if chapel.select_date("18-06-2025"):
                    print("Date selection successful!")
                    chapel.book_court("21:00")
                else:
                    print("Date selection failed!")
            else:
                print("Court type selection failed!")
        else:
            print("Login failed")
    except Exception as e:
        print(f"Error during test: {str(e)}")
    finally:
        print("Closing browser session")
        chapel.close()

if __name__ == "__main__":
    main() 