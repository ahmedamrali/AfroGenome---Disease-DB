import time
from Bio.Seq import Seq
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import pandas as pd
import zipfile
import sqlite3
import shutil


class NCBIBot:
    def __init__(self):
        # Set up Firefox WebDriver with preferences
        self.raw_data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw data")
        self.create_raw_data_folder()

        self.firefox_profile = webdriver.FirefoxProfile()
        self.firefox_profile.set_preference("browser.download.dir", self.raw_data_folder)
        self.firefox_profile.set_preference("browser.download.folderList", 2)  # 2 means custom location
        self.firefox_profile.set_preference("browser.download.manager.showWhenStarting", False)
        self.firefox_profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

        # Create Firefox options and set the profile
        self.firefox_options = Options()
        self.firefox_options.profile = self.firefox_profile

        # Create the Firefox WebDriver with the configured profile and options
        self.driver = webdriver.Firefox(options=self.firefox_options)
        self.driver.get("https://www.ncbi.nlm.nih.gov/gene")

    def create_raw_data_folder(self):
        if not os.path.exists(self.raw_data_folder):
            os.makedirs(self.raw_data_folder)

    def download_data(self, gene, disease_name):
        full_data_dict = {"DNA Sequences": [], "mRNA Sequences": [], "Protein Sequences": [],
                          "disease": disease_name, "gene": gene}
        # Wait for the element to be clickable
        time.sleep(5)

        search_box = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.jig-ncbiclearbutton.jig-ncbiautocomplete"))
        )

        search_box.send_keys(gene)
        search_button = self.driver.find_element(By.CSS_SELECTOR, "#search.button_search.nowrap")
        search_button.click()

        try:
            find_gene_link = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a#feat_gene_title"))
            )
        except:
            find_gene_link = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.LINK_TEXT, gene))
            )

        find_gene_link.click()

        time.sleep(10)

        exon_count = self.driver.find_element(By.XPATH, "//dt[text()='Exon count: ']")
        if exon_count:
            exon_count = exon_count.find_element(By.XPATH, "following-sibling::dd").text

        summary_tag = self.driver.find_element(By.XPATH, "//dt[text()='Summary']")
        if summary_tag:
            summary_text = summary_tag.find_element(By.XPATH, "following-sibling::dd").text
            full_data_dict["Summary"] = summary_text

        exp_tag = self.driver.find_element(By.XPATH, "//dt[text()='Expression']")
        if exp_tag:
            exp_text = exp_tag.find_element(By.XPATH, "following-sibling::dd").text
            full_data_dict["Expression"] = exp_text.replace("See more", "")

        self.download_datasets()

        current_directory = os.getcwd()
        data_folder = os.path.join(current_directory, "data")
        raw_data_folder = os.path.join(data_folder, "raw data")

        zip_file = [file for file in os.listdir(raw_data_folder) if file.endswith('.zip')]

        if zip_file:
            zip_file_path = os.path.join(raw_data_folder, zip_file[0])

            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(raw_data_folder)

            os.remove(zip_file_path)
            readme_file_path = os.path.join(raw_data_folder, "README.md")
            if os.path.exists(readme_file_path):
                os.remove(readme_file_path)

        enter_data_1 = os.path.join(raw_data_folder, "ncbi_dataset")
        enter_data_2 = os.path.join(enter_data_1, "data")
        extracted_files = os.listdir(enter_data_2)
        dna_sequences = []
        mrna_sequences = []
        protein_sequences = []
        for extracted_file in extracted_files:
            if extracted_file.startswith("gene"):
                file_path = os.path.join(enter_data_2, extracted_file)
                with open(file_path, "r") as read:
                    content = read.readlines()
                    for line in content:
                        if line.startswith('>'):
                            continue
                        seq = line.strip()
                        dna_sequences.append(seq)
                        seq_object = Seq(seq)
                        mrna_sequences.append(str(seq_object.transcribe()))

                        if len(seq_object) % 3 != 0:
                            seq_object = seq_object[:-(len(seq_object) % 3)]

                        protein_sequences.append(str(seq_object.translate()))

        full_data_dict["DNA Sequences"] = ''.join(dna_sequences)
        full_data_dict["mRNA Sequences"] = ''.join(mrna_sequences)
        full_data_dict["Protein Sequences"] = ''.join(protein_sequences)
        full_data_dict["Exon Count"] = exon_count

        if os.path.exists(enter_data_1):
            shutil.rmtree(enter_data_1)

        return full_data_dict

    def download_datasets(self):
        click_on_download = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Download Datasets"))
        )
        click_on_download.click()

        final_download = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#datasets-download-submit"))
        )
        final_download.click()

        time.sleep(5)


class GeneDatabase:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)
        self.cursor = self.connection.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS genes_data (
                Disease_Name TEXT,
                Gene TEXT,
                DNA_Sequence TEXT,
                mRNA_Sequence TEXT,
                Protein_Sequence TEXT,
                Expression TEXT,
                Summary TEXT,
                Exon_Count TEXT
            )
        ''')
        self.connection.commit()

    def insert_data(self, full_data_dict):
        self.cursor.execute('''
            SELECT COUNT(*) FROM genes_data
            WHERE Disease_Name = ? AND Gene = ?
        ''', (full_data_dict["disease"], full_data_dict["gene"]))

        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO genes_data (
                    Disease_Name, Gene, DNA_Sequence, mRNA_Sequence, Protein_Sequence, Expression, Summary, Exon_Count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                full_data_dict["disease"],
                full_data_dict["gene"],
                full_data_dict["DNA Sequences"],
                full_data_dict["mRNA Sequences"],
                full_data_dict["Protein Sequences"],
                full_data_dict["Expression"],
                full_data_dict["Summary"],
                full_data_dict["Exon Count"]
            ))

            self.connection.commit()

    def close_connection(self):
        self.connection.close()


# Example Usage:

# Initialize NCBIBot and GeneDatabase instances
ncbi_bot = NCBIBot()
gene_database = GeneDatabase(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "genes_data.db"))

# Iterate over data_dict
for key, values in data_dict.items():
    disease_name = key
    genes = values
    for gene in genes:
        # Download data using NCBIBot
        full_data_dict = ncbi_bot.download_data(gene, disease_name)

        # Insert data into the database using GeneDatabase
        gene_database.insert_data(full_data_dict)

# Close the database connection
gene_database.close_connection()
