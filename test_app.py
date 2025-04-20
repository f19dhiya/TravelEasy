import unittest
import time
# Removed unused sys import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service # Or Firefox/Edge service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Optional: Specify WebDriver path if not in PATH
# webdriver_path = '/path/to/your/chromedriver'
# service = Service(executable_path=webdriver_path)

class TravelEasyAppTests(unittest.TestCase):

    # ... (setUp, tearDown, _login remain the same) ...
    def setUp(self):
        # Initialize WebDriver (using Chrome in this example)
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') # Optional: Run headless
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        # Use WebDriverWait instead of implicit wait for more control
        self.wait = WebDriverWait(self.driver, 10) # Wait up to 10 seconds
        self.base_url = "http://127.0.0.1:5000" # Assuming app runs locally on port 5000
        # No initial navigation here, start fresh in the test

    def tearDown(self):
        # Close the browser window
        self.driver.quit()

    def _login(self, username="admin", password="admin"): # Default credentials
        """Helper method to log in."""
        driver = self.driver
        driver.get(self.base_url + "/login") # Ensure we start at login page
        print(f"Attempting login as '{username}'...")

        # Find login form elements using WebDriverWait
        username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
        submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Sign In']")))

        username_field.clear() # Clear fields in case of reuse
        password_field.clear()
        username_field.send_keys(username)
        password_field.send_keys(password)
        submit_button.click()

        try:
            # 1. Wait for the dashboard URL
            self.wait.until(EC.url_to_be(self.base_url + "/dashboard"))

            # 2. Wait for the presence of the container element using its class
            container_xpath = "//div[contains(@class, 'user-greeting')]"
            welcome_container = self.wait.until(EC.presence_of_element_located((By.XPATH, container_xpath)))

            # 3. Verify the text within the container
            container_text = welcome_container.text
            if not ("Welcome back," in container_text and username in container_text):
                self.fail(f"Login Succeeded (URL is /dashboard), but container text did not match. Expected 'Welcome back, {username}'. Found text: '{container_text}'")
            print(f"Login successful for '{username}'.")

        except TimeoutException:
            # If either wait above times out, THEN check if it was a login failure
            current_url_after_wait = driver.current_url
            if "/dashboard" not in current_url_after_wait:
                try:
                    self.wait.until(EC.url_contains("/login")) # Check if back on login page
                    error_message = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'alert-danger')]")))
                    self.fail(f"Login failed for '{username}'. Found error message: '{error_message.text}'")
                except TimeoutException:
                    self.fail(f"Login failed for '{username}'. Did not redirect to /dashboard or show error on /login. Current URL: {current_url_after_wait}")
                except NoSuchElementException:
                     self.fail(f"Login failed for '{username}'. Redirected back to /login but no error message found. Current URL: {current_url_after_wait}")
            else:
                self.fail(f"Login Succeeded for '{username}' (URL is /dashboard), but failed to find welcome container element with XPath: {container_xpath}. Current URL: {current_url_after_wait}")
        except Exception as e:
            self.fail(f"An unexpected error occurred during login verification for '{username}': {e}")


    def test_signup_and_login(self):
        """Tests signing up a new user and then logging in with those credentials."""
        # ... (test_signup_and_login remains the same) ...
        print("Running test_signup_and_login...")
        driver = self.driver
        driver.get(self.base_url + "/login") # Start at login page for signup link

        # --- Sign Up Phase ---
        print("Navigating to signup page...")
        signup_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Create Account']")))
        signup_link.click()

        self.wait.until(EC.url_to_be(self.base_url + "/signin"))
        self.assertEqual(driver.current_url, self.base_url + "/signin")
        print("On signup page.")

        # Generate unique credentials for signup
        timestamp = int(time.time())
        new_username = f"testuser_{timestamp}" # Make username more specific
        new_email = f"testuser_{timestamp}@example.com"
        new_password = "testpassword123"
        print(f"Generated credentials: Username='{new_username}', Email='{new_email}'")

        # Find signup form elements
        username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_field = self.wait.until(EC.presence_of_element_located((By.ID, "password")))
        submit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Create Account']")))

        # Enter new user details
        username_field.send_keys(new_username)
        email_field.send_keys(new_email)
        password_field.send_keys(new_password)
        print("Submitting signup form...")
        submit_button.click()

        # Wait for redirection back to login page after signup
        self.wait.until(EC.url_to_be(self.base_url + "/login"))
        print("Signup successful, redirected to login page.")
        # --- End Sign Up Phase ---

        # --- Login Phase ---
        # Now, use the _login helper with the newly created credentials
        self._login(new_username, new_password)
        # --- End Login Phase ---

        print("test_signup_and_login PASSED")

    def test_add_package_to_cart(self):
        """Tests adding a package to the cart and verifying it."""
        print("Running test_add_package_to_cart...")
        driver = self.driver
        self._login("admin", "admin")

        print("Finding 'Book Now' button for the first package...")
        book_button_locator = (By.XPATH, "(//button[normalize-space()='Book Now'])[1]")
        book_button = self.wait.until(EC.presence_of_element_located(book_button_locator))
        package_card = driver.find_element(By.XPATH, "(//div[contains(@class, 'dashboard-card')])[1]")
        package_name = package_card.find_element(By.XPATH, ".//h5[@class='card-title']").text
        print(f"Found package: {package_name}. Attempting to click 'Book Now'...")

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", book_button)
            time.sleep(0.5)
            clickable_book_button = self.wait.until(EC.element_to_be_clickable(book_button_locator))
            clickable_book_button.click()
            print("Book Now clicked successfully.")
        except ElementClickInterceptedException:
            print("Standard click failed due to interception. Trying JavaScript click...")
            try:
                driver.execute_script("arguments[0].click();", book_button)
                print("Book Now clicked using JavaScript.")
            except Exception as js_e:
                self.fail(f"Both standard and JavaScript clicks failed for 'Book Now' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"An unexpected error occurred when trying to click 'Book Now': {e}")

        # **** ADDED PAUSE ****
        time.sleep(0.5) # Short pause for DOM to stabilize after booking click

        print("Navigating to cart...")
        cart_button_locator = (By.XPATH, "//a[normalize-space()='View Cart']")
        try:
            # Wait for clickable and then click
            cart_button = self.wait.until(EC.element_to_be_clickable(cart_button_locator))
            cart_button.click()
        except TimeoutException:
             self.fail("Timed out waiting for 'View Cart' button to be clickable.")
        except ElementClickInterceptedException:
             print("Standard click failed for View Cart. Trying JS click...")
             try:
                 # Find the element again before JS click, just in case
                 cart_button_element = self.wait.until(EC.presence_of_element_located(cart_button_locator))
                 driver.execute_script("arguments[0].click();", cart_button_element)
                 print("View Cart clicked using JavaScript.")
             except Exception as js_e:
                 self.fail(f"Both clicks failed for 'View Cart' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking 'View Cart': {e}")


        self.wait.until(EC.url_to_be(self.base_url + "/cart"))
        self.assertEqual(driver.current_url, self.base_url + "/cart")
        print("On cart page.")

        try:
            print(f"Verifying if '{package_name}' is in the cart...")
            cart_item_title = self.wait.until(EC.presence_of_element_located((By.XPATH, f"//h3[@class='cart-item-title' and contains(text(), '{package_name}')]")))
            self.assertIsNotNone(cart_item_title, f"{package_name} not found in cart")
            print(f"'{package_name}' found in cart.")
        except TimeoutException:
            self.fail(f"Timed out waiting for package '{package_name}' to appear in the cart.")
        except NoSuchElementException:
            self.fail(f"Package '{package_name}' was not found in the cart using XPath.")

        print("test_add_package_to_cart PASSED")

    def test_book_package_and_verify_history(self):
        """Tests the full flow: book, checkout, verify bill, verify history."""
        print("Running test_book_package_and_verify_history...")
        driver = self.driver
        package_to_book = "Paris"
        self._login("admin", "admin")

        print(f"Finding 'Book Now' for {package_to_book}...")
        book_button_locator = (By.XPATH, f"//div[contains(@class, 'dashboard-card')][.//h5[contains(text(), '{package_to_book}')]]//button[normalize-space()='Book Now']")
        book_button = self.wait.until(EC.presence_of_element_located(book_button_locator))

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", book_button)
            time.sleep(0.5)
            clickable_book_button = self.wait.until(EC.element_to_be_clickable(book_button_locator))
            clickable_book_button.click()
            print(f"Book Now clicked for {package_to_book}.")
        except ElementClickInterceptedException:
            print("Standard click failed for Book Now. Trying JS click...")
            try:
                driver.execute_script("arguments[0].click();", book_button)
                print("Book Now clicked using JavaScript.")
            except Exception as js_e:
                self.fail(f"Both clicks failed for 'Book Now' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking 'Book Now': {e}")

        # **** ADDED PAUSE ****
        time.sleep(0.5) # Short pause for DOM to stabilize after booking click

        print("Navigating to cart...")
        cart_button_locator = (By.XPATH, "//a[normalize-space()='View Cart']")
        try:
            # Wait for clickable and then click
            cart_button = self.wait.until(EC.element_to_be_clickable(cart_button_locator))
            cart_button.click()
        except TimeoutException:
             self.fail("Timed out waiting for 'View Cart' button to be clickable.")
        except ElementClickInterceptedException:
             print("Standard click failed for View Cart. Trying JS click...")
             try:
                 # Find the element again before JS click, just in case
                 cart_button_element = self.wait.until(EC.presence_of_element_located(cart_button_locator))
                 driver.execute_script("arguments[0].click();", cart_button_element)
                 print("View Cart clicked using JavaScript.")
             except Exception as js_e:
                 self.fail(f"Both clicks failed for 'View Cart' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking 'View Cart': {e}")

        self.wait.until(EC.url_to_be(self.base_url + "/cart"))
        print("On cart page.")

        # ... (rest of test_book_package_and_verify_history remains the same) ...
        # 4. Proceed to Checkout
        print("Proceeding to checkout...")
        checkout_button_locator = (By.XPATH, "//a[contains(@class, 'checkout-btn')]")
        checkout_button = self.wait.until(EC.presence_of_element_located(checkout_button_locator))
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", checkout_button)
            time.sleep(0.5)
            clickable_checkout_button = self.wait.until(EC.element_to_be_clickable(checkout_button_locator))
            clickable_checkout_button.click()
            print("Proceed to Checkout clicked.")
        except ElementClickInterceptedException:
             print("Standard click failed for Checkout. Trying JS click...")
             try:
                 driver.execute_script("arguments[0].click();", checkout_button)
                 print("Checkout clicked using JavaScript.")
             except Exception as js_e:
                 self.fail(f"Both clicks failed for 'Checkout' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking 'Checkout': {e}")

        # 5. Confirm Payment Method
        self.wait.until(EC.url_to_be(self.base_url + "/payment"))
        print("On payment page. Confirming payment method...")
        # Assuming default (Credit Card) is selected, find and click confirm button
        confirm_payment_button_locator = (By.XPATH, "//button[contains(@class, 'submit-btn')]")
        confirm_payment_button = self.wait.until(EC.presence_of_element_located(confirm_payment_button_locator))
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", confirm_payment_button)
            time.sleep(0.5)
            clickable_confirm_button = self.wait.until(EC.element_to_be_clickable(confirm_payment_button_locator))
            clickable_confirm_button.click()
            print("Confirm Payment Method clicked.")
        except ElementClickInterceptedException:
             print("Standard click failed for Confirm Payment. Trying JS click...")
             try:
                 driver.execute_script("arguments[0].click();", confirm_payment_button)
                 print("Confirm Payment clicked using JavaScript.")
             except Exception as js_e:
                 self.fail(f"Both clicks failed for 'Confirm Payment' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking 'Confirm Payment': {e}")

        # 6. Verify Bill Page (Generated after payment)
        self.wait.until(EC.url_to_be(self.base_url + "/bill")) # Wait for the immediate bill page
        print("On immediate bill page after payment.")
        try:
            # Check for the specific header text on the bill page generated right after payment
            bill_header = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='bill-header']/h2")))
            # **** FIX: Expect "Booking Confirmation" on the immediate bill page ****
            self.assertIn("Booking Confirmation", bill_header.text, "Immediate bill page header does not contain 'Booking Confirmation'")
            print("Verified 'Booking Confirmation' text on immediate bill page.")
        except TimeoutException:
            self.fail("Timed out waiting for immediate bill page header.")
        except NoSuchElementException:
            self.fail("Could not find immediate bill page header element.")

        # 7. Navigate Back to Dashboard
        print("Navigating back to dashboard...")
        back_button_locator = (By.XPATH, "//a[contains(@class, 'btn-primary') and normalize-space()='Back to Dashboard']")
        # Find the element first
        back_to_dashboard_button = self.wait.until(EC.presence_of_element_located(back_button_locator))

        try:
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", back_to_dashboard_button)
            time.sleep(0.5)
            # Wait until clickable *after* scrolling
            clickable_back_button = self.wait.until(EC.element_to_be_clickable(back_button_locator))
            clickable_back_button.click()
            print("Back to Dashboard button clicked successfully.")
        except ElementClickInterceptedException:
            print("Standard click failed for Back to Dashboard. Trying JS click...")
            try:
                # Fallback: Use JavaScript click
                driver.execute_script("arguments[0].click();", back_to_dashboard_button)
                print("Back to Dashboard clicked using JavaScript.")
            except Exception as js_e:
                self.fail(f"Both clicks failed for 'Back to Dashboard' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking 'Back to Dashboard': {e}")

        # Wait for dashboard URL after click
        self.wait.until(EC.url_to_be(self.base_url + "/dashboard"))
        print("On dashboard page.")

        # 8. Verify Booking History
        print(f"Verifying '{package_to_book}' in booking history...")
        try:
            # Look for the list group item containing the package name
            history_item_locator = (By.XPATH, f"//div[contains(@class, 'list-group')]//a[contains(@class, 'list-group-item')][.//h5[contains(text(), '{package_to_book}')]]")
            history_item = self.wait.until(EC.presence_of_element_located(history_item_locator))
            self.assertIsNotNone(history_item, f"Booking history item for '{package_to_book}' not found.")
            # Optionally check status
            status_element = history_item.find_element(By.XPATH, ".//small[contains(@class, 'text-success')]") # Assuming completed status
            self.assertIn("Completed", status_element.text, "Booking status is not 'Completed' in history.")
            print(f"'{package_to_book}' found in booking history with correct status.")
        except TimeoutException:
            self.fail(f"Timed out waiting for booking history item for '{package_to_book}'.")
        except NoSuchElementException:
            self.fail(f"Could not find booking history item or status for '{package_to_book}'.")

        print("test_book_package_and_verify_history PASSED")


    def test_view_history_and_print_bill(self):
        """Tests viewing a booking from history and attempting to print the bill."""
        # ... (test_view_history_and_print_bill remains the same, including the 3 sec delay) ...
        print("Running test_view_history_and_print_bill...")
        driver = self.driver
        package_name_in_history = "Paris" # Package to look for in history

        # 1. Login
        self._login("admin", "admin") # Ensure admin user exists

        # 2. Find and Click History Item
        print(f"Finding '{package_name_in_history}' in booking history...")
        history_item_locator = (By.XPATH, f"//div[contains(@class, 'list-group')]//a[contains(@class, 'list-group-item')][.//h5[contains(text(), '{package_name_in_history}')]]")
        try:
            history_item = self.wait.until(EC.presence_of_element_located(history_item_locator))
            # Get the expected bill URL from the link's href
            # expected_bill_url = history_item.get_attribute('href') # Not strictly needed if using url_matches
            print(f"Found history item for '{package_name_in_history}'. Clicking...")

            # Scroll and click the history item
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", history_item)
            time.sleep(0.5)
            clickable_history_item = self.wait.until(EC.element_to_be_clickable(history_item_locator))
            clickable_history_item.click()

        except TimeoutException:
            self.fail(f"Timed out waiting for booking history item for '{package_name_in_history}'. Ensure this booking exists.")
        except NoSuchElementException:
            self.fail(f"Could not find booking history item for '{package_name_in_history}'. Ensure this booking exists.")
        except ElementClickInterceptedException:
             print("Standard click failed for history item. Trying JS click...")
             try:
                 driver.execute_script("arguments[0].click();", history_item)
                 print("History item clicked using JavaScript.")
             except Exception as js_e:
                 self.fail(f"Both clicks failed for history item. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking history item: {e}")

        # 3. Verify Navigation to Bill Page (from History)
        try:
            # Wait for the URL to match the pattern /bill/some_id
            self.wait.until(EC.url_matches(f"{self.base_url}/bill/\\d+"))
            print(f"Navigated to bill page from history: {driver.current_url}")
            # Also verify the header again for certainty
            bill_header = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='bill-header']/h2")))
            # **** FIX: Expect "Booking Details" when viewing from history ****
            self.assertIn("Booking Details", bill_header.text, "Bill page header is incorrect when viewing from history.")
            print("Verified 'Booking Details' text on bill page from history.")
        except TimeoutException:
            self.fail(f"Did not navigate to the expected bill page URL pattern from history. Current URL: {driver.current_url}")

        # 4. Find and Click Print Bill Button
        print("Finding 'Print Bill' button...")
        # Corrected XPath for the print button based on bill.html
        print_button_locator = (By.XPATH, "//button[contains(@class, 'btn-outline') and contains(., 'Print Bill')]")
        try:
            print_button = self.wait.until(EC.presence_of_element_located(print_button_locator))

            # Scroll and click
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", print_button)
            time.sleep(0.5)
            clickable_print_button = self.wait.until(EC.element_to_be_clickable(print_button_locator))
            clickable_print_button.click()
            print("Clicked 'Print Bill' button. Assuming print dialog was triggered (cannot verify directly).")
            # **** ADDED DELAY ****
            print("Waiting 3 seconds after print click...")
            time.sleep(3)

        except TimeoutException:
            self.fail("Timed out waiting for 'Print Bill' button.")
        except ElementClickInterceptedException:
             print("Standard click failed for Print Bill. Trying JS click...")
             try:
                 driver.execute_script("arguments[0].click();", print_button)
                 print("Print Bill clicked using JavaScript. Assuming print dialog was triggered.")
                 # **** ADDED DELAY ****
                 print("Waiting 3 seconds after print click...")
                 time.sleep(3)
             except Exception as js_e:
                 self.fail(f"Both clicks failed for 'Print Bill' button. JS Error: {js_e}")
        except Exception as e:
             self.fail(f"Error clicking 'Print Bill' button: {e}")

        # 5. Test Conclusion (No direct dialog verification possible)
        print("test_view_history_and_print_bill PASSED (Print dialog trigger assumed)")

    def test_logout(self):
        """Tests logging out from the dashboard."""
        # ... (test_logout remains the same) ...
        print("Running test_logout...")
        driver = self.driver

        # 1. Login
        self._login("admin", "admin") # Ensure admin user exists

        # 2. Find and Click Logout Button
        print("Finding logout button on dashboard...")
        # XPath based on dashboard.html: <a href="/logout" class="btn btn-danger">...Logout</a>
        logout_button_locator = (By.XPATH, "//a[contains(@class, 'btn-danger') and contains(., 'Logout')]")
        try:
            # Wait for the button to be clickable
            logout_button = self.wait.until(EC.element_to_be_clickable(logout_button_locator))
            print("Logout button found. Clicking...")
            logout_button.click()
        except TimeoutException:
            self.fail("Timed out waiting for the logout button on the dashboard.")
        except NoSuchElementException:
            self.fail("Could not find the logout button on the dashboard.")
        except Exception as e:
            self.fail(f"An error occurred clicking the logout button: {e}")

        # 3. Verify Redirection to Login Page
        try:
            # Wait for the URL to become the login page URL
            self.wait.until(EC.url_to_be(self.base_url + "/login"))
            print(f"Successfully redirected to login page: {driver.current_url}")
            # Optionally, check for a known element on the login page
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//h2[normalize-space()='Welcome Back']")))
            print("Verified presence of login page header.")
        except TimeoutException:
            self.fail(f"Did not redirect to the login page after logout. Current URL: {driver.current_url}")

        print("test_logout PASSED")


if __name__ == "__main__":
    # IMPORTANT: Ensure you have a user 'admin' with password 'admin' in your DB
    # AND that this user has a completed booking for 'Paris' in their history.
    # Reverted to standard unittest.main for running via `python -m unittest`
    unittest.main(verbosity=2)