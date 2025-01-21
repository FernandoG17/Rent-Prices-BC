import csv
from email.message import EmailMessage
import smtplib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import datetime
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

#-------------------------------Selenium Code ----------------------------------------
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

#Create and configure the Chrome webdriver
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://rentals.ca/vancouver")
cookies = driver.find_element(By.XPATH, '//*[@id="ez-cookie-notification__accept"]')
cookies.click()

csv_file = "housing_data.csv"
excel_file = "housing_data.csv.xlsx"
all_data = []
beds = []
clean_beds = []

#---------------------------------Getting Information--------------------------------------------------------
def retrieve_housing_data():
    cities = ["Vancouver", "Burnaby", "Surrey", "Richmond"]
    global data, count

    for city in cities:
        print(f"Locating at {city}")
        driver.get(f"https://rentals.ca/{city}")

        for press in range(7):
            print(f"Looking in {press}...")
            price = driver.find_elements(By.CSS_SELECTOR, "p.listing-card__price.d-inline-block")
            num_of_beds = driver.find_elements(By.CSS_SELECTOR, "ul.listing-card__main-features > li:first-child")
            type_listing = driver.find_elements(By.CLASS_NAME, "listing-card__type")

            for b in range(len(num_of_beds)):
                clean_beds.append(num_of_beds[b].text.replace("BED", "").replace("-", "").strip().split())

            for n in range(len(clean_beds)):
                for item in range(len(clean_beds[n])):
                    if clean_beds[n][item] == '0':
                        clean_beds[n][item] = '1'
                    temp= clean_beds[n][item]
                    clean_beds[n][item] = int(float(temp))

            for n in range(len(clean_beds)):
                total = 0
                for item in range(len(clean_beds[n])):
                    total += clean_beds[n][item]
                    total = total/len(clean_beds[n])
                beds.append(round(total))

            for n in range(len(price)):
                clean_price = price[n].text.replace("$", "").replace("-", "").replace("0","").strip().split(" ")
                average_price  = (int(clean_price[0]) + int(clean_price[-1]))/2

                listing = {
                    "City": city,
                    "Price": average_price,
                    "Beds": beds[n],
                    "Type": type_listing[n].text if n < len(type_listing) else "N/A",
                }
                all_data.append(listing)
            next = driver.find_element(By.CSS_SELECTOR, "ul.pagination li.pagination__item a")
            next.click()
    return (all_data)

#---------------------------------Convert Data Into csv and xlsx------------------------------------------

def convert_to_csv(data):
    df = pd.DataFrame(data)

    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

    # Filter rows where price is greater than or equal to 400
    df = df[df['Price'] >= 400]


    df.to_csv(csv_file, index = False)
    df.to_excel(excel_file, index = False)
    print("Saved files")

#---------------------------------Send information via Email ------------------------------------------------------

def send_email():
    sender_email = os.getenv("sender_email")
    password = os.getenv("password")
    to_email = os.getenv("to_email")
    subject = "Housing Data CSV"
    body = "CSV file for housing data is ready"

    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    #Attach the Excel file
    with open(csv_file, 'rb') as file:
        msg.add_attachment(file.read(), maintype='application', subtype='csv', filename= csv_file)

    with smtplib.SMTP('smtp.gmail.com', 587) as connection:
        connection.starttls()  # Start TLS encryption
        connection.login(user=sender_email, password=password)  # Log in
        connection.send_message(msg)  # Send the email
    print("Email sent successfully!")
#---------------------------------------------Clean Data----------------------------------------------------------------------------

data = retrieve_housing_data()
convert_to_csv(data)
send_email()
print("Done")