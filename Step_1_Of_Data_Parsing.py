# We import what is wanted from selenium and time
from selenium import webdriver
from selenium.common import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import os


# We make a class for the bot that we are using
class DisGeNETBot:
    # We define the constructor and have it call the driver we are going to use
    def __init__(self):
        # Specify the download directory
        self.download_directory = os.path.join(os.path.dirname(os.path.abspath(__file__))
                                               , "data", "excel sheets")

        # Create "data" and "excel sheets" folders if they don't exist
        os.makedirs(self.download_directory, exist_ok=True)

        # Create a Firefox profile with the desired settings
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("browser.download.dir", self.download_directory)
        firefox_profile.set_preference("browser.download.folderList", 2)  # 2 means custom location
        firefox_profile.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                                       "application/octet-stream")

        # Create Firefox options and set the profile
        firefox_options = Options()
        firefox_options.profile = firefox_profile

        # Create the Firefox WebDriver with the configured profile and options
        self.driver = webdriver.Firefox(options=firefox_options)

    # We define the login method that will take the email and password and use them to log in
    def login(self, username, password):
        # We ask the driver to go to our wanted link
        self.driver.get("https://www.disgenet.org/login/")
        # We as the driver to find the username box by looking for its name and the same
        # for the password
        search = self.driver.find_element(By.NAME, "username")
        # We then send the username that we are going to specify
        # and the same for the password
        search.send_keys(username)
        search = self.driver.find_element(By.NAME, "password")
        search.send_keys(password)
        # We give the bot sometime to reduce errors causes by internet speed and whatnot
        # to find the submit button by its class name
        submit = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "col-lg-12"))
        )
        submit.submit()
        # We stop the code for 20 seconds to make sure that the website loads to
        # avoid errors
        time.sleep(20)

    # We make a method to navigate to click on the search button and wait until it is
    # clickable before clicking it in the first place
    # it is found by its XPATH since it doesn't have other specifc info
    def navigate_to_search(self):
        search_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='/search']"))
        )
        search_button.click()

    # We make a method to search for the disease by finding the search box
    def search_disease(self, disease):
        # The search box is found by its ID and we wait 10 seconds until it is found to
        # avoid errors
        search = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "search_id"))
        )
        # The search box is cleared
        search.clear()
        # The disease name is written in it
        search.send_keys(disease)
        time.sleep(10)
        # We find the submit button for the search and click on it
        submit = self.driver.find_element(By.ID, "id_submit")
        submit.click()

    # We make a method to open the summary of the genes related to the disease webpage
    def navigate_to_summary_of_gene_disease(self):
        try:
            # As done before by waiting for the wanted button clickable, we find the
            # button by text and make sure that the button is view by asking the bot
            # to scroll
            summary_of_gene_disease = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Summary of Gene-Disease Associations"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView();",
                                       summary_of_gene_disease)
            self.driver.execute_script("window.scrollBy(0, -200);")
            time.sleep(10)
            ActionChains(self.driver).move_to_element(summary_of_gene_disease).click().perform()

        except UnexpectedAlertPresentException as alert_ex:
            # If an alert is present, print the alert text, dismiss it, and wait for it to disappear
            print("Alert present. Alert text:", alert_ex.alert_text)

            # Get the alert object and dismiss it
            alert = self.driver.switch_to.alert
            alert.dismiss()

            # Wait for the alert to disappear
            WebDriverWait(self.driver, 10).until_not(EC.alert_is_present())
            print("Alert dismissed")

        except Exception as e:
            # Handle any other exceptions that might occur
            print(f"An error occurred: {e}")

    # We make a method to press on our download button
    def download_gene_data(self):
        # We wait until the first download button is clickable and find it by its XPATH
        # and click on it
        download_button1 = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-default' and"
                                                  " @data-toggle='modal'"
                                                  " and @data-target='#download-modal']"))
        )
        download_button1.click()

        # We wait until the secobd download button is clickable and find it by its XPATH
        download_button2 = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn.dsgn-button"))
        )
        download_button2.click()
        # We stop the code for 10 seconds to make sure that the file is downloaded
        time.sleep(10)

    # We make a method to go back to the search page and search for the other diseases
    # in the list
    def navigate_back(self):
        self.driver.back()
        time.sleep(10)
        self.driver.back()

    # We make a method to quit the bot
    def quit(self):
        self.driver.quit()


# We ask python to start our code and call for our bot class
if __name__ == "__main__":
    bot = DisGeNETBot()

    try:
        bot.login("indraandashora@gmail.com", "Aa421972")
        bot.navigate_to_search()

        disease_list = ["Mental Retardation", "Convulsive disorder", "Microcephaly", "Hydrocephalus",
                        "Craniosynostosis", "Neural tube defects", "Neurodegenerative disorders",
                        "Neurocutaneous Syndromes", "Anemia, Sickle Cell", "alpha-Thalassemia", "Hemophilia A",
                        "Aplastic anemia", "Thrombasthenia", " Down syndrome", "Inborn Errors Of Metabolism	",
                        "Histidinemia", "Neuromuscular Diseases", "Congenital myopathy (disorder)",
                        "Skin Diseases, Genetic", "Histidinemia"]

        for disease in disease_list:
            bot.search_disease(disease)
            bot.navigate_to_summary_of_gene_disease()
            bot.download_gene_data()
            bot.navigate_back()

    finally:
        bot.quit()
