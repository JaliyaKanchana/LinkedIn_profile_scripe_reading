import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import time

with open('credentials_and_urls.json') as json_file:
    data = json.load(json_file)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
driver = webdriver.Chrome(options=chrome_options)

def wait_for_correct_current_url(desired_url):
    while driver.current_url != desired_url:
        time.sleep(0.01)

url = 'https://www.linkedin.com/login'
driver.get(url)
time.sleep(2)
username = data["login_credentials"]["username"]
password = data["login_credentials"]["password"]

uname = driver.find_element(By.ID, "username")
uname.send_keys(username)
time.sleep(2)
pword = driver.find_element(By.ID, "password")
pword.send_keys(password)
time.sleep(2)

driver.find_element(By.XPATH, "//button[@type='submit']").click()
desired_url = 'https://www.linkedin.com/feed/'
wait_for_correct_current_url(desired_url)

profiles_data = []

for profile_url in data["profile_urls"]:
    profile_data = {'Name': '', 'Company': '', 'Location': '', 'Experience': [], 'Education': []}
    driver.get(profile_url)
    time.sleep(3)  # Adjust timing as needed for the page to load

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    intro = soup.find('div', {'class': 'mt2 relative'})
    name_loc = intro.find('h1') if intro else None
    profile_data['Name'] = name_loc.text.strip() if name_loc else ''

    company_loc = soup.find('div', class_='text-body-medium')
    profile_data['Company'] = company_loc.text.strip() if company_loc else ''

    location_loc = intro.find_all('span', {'class': 'text-body-small'}) if intro else []
    profile_data['Location'] = location_loc[0].text.strip() if location_loc else ''

    # Process Experience Section
    experience_section = soup.find(lambda tag: tag.name == 'section' and tag.find('div', {'id': 'experience'}))
    if experience_section:
        experiences = experience_section.find_all('li', {'class': 'artdeco-list__item'})
        for exp in experiences:
            exp_data = {}
            exp_data['Job Title'] = exp.find('span').text.strip() if exp.find('span') else ''
            # Assuming company and date are in 't-14' spans; adjust as needed
            company_exp_elements = exp.find_all('span', class_='t-14')
            exp_data['Company'] = company_exp_elements[0].text.strip() if len(company_exp_elements) > 0 else ''
            exp_data['Date'] = company_exp_elements[1].text.strip() if len(company_exp_elements) > 1 else ''
            profile_data['Experience'].append(exp_data)

    # Process Education Section (similar logic to Experience)
    education_section = soup.find(lambda tag: tag.name == 'section' and tag.find('div', {'id': 'education'}))
    if education_section:
        educations = education_section.find_all('li', {'class': 'artdeco-list__item'})
        for edu in educations:
            edu_data = {}
            edu_data['School Name'] = edu.find('span', {'class': 't-bold'}).text.strip() if edu.find('span', {'class': 't-bold'}) else ''
            edu_data['Degree Name'] = edu.find('span', {'class': 't-14'}).text.strip() if edu.find('span', {'class': 't-14'}) else ''
            edu_field_of_study = edu.find('span', {'class': 'pv-entity__comma-item'})
            edu_data['Field of Study'] = edu_field_of_study.text.strip() if edu_field_of_study else ''
            edu_dates = edu.find_all('span', class_='visually-hidden')
            edu_data['Dates Attended'] = edu_dates[-1].text.strip() if edu_dates else ''  # Assuming the last 'visually-hidden' span contains the date
            profile_data['Education'].append(edu_data)

    profiles_data.append(profile_data)

    # Print the collected profile data to the terminal
    print(f"\nScraped Profile Data:")
    print(f"Name: {profile_data['Name']}")
    print(f"Company: {profile_data['Company']}")
    print(f"Location: {profile_data['Location']}")
    print("Experience:")
    for exp in profile_data['Experience']:
        print(f" - Job Title: {exp['Job Title']}, Company: {exp['Company']}, Date: {exp['Date']}")
    print("Education:")
    for edu in profile_data['Education']:
        print(f" - School Name: {edu['School Name']}, Degree Name: {edu['Degree Name']}, Field of Study: {edu['Field of Study']}, Dates Attended: {edu['Dates Attended']}")

# Closing the driver after scraping
driver.quit()

# Convert the scraped data to a pandas DataFrame
profiles_df = pd.DataFrame.from_records(profiles_data)

# Expand 'Experience' and 'Education' lists into string representations for CSV
profiles_df['Experience'] = profiles_df['Experience'].apply(lambda x: '\n'.join([f"{exp['Job Title']} at {exp['Company']}, {exp['Date']}" for exp in x]) if x else '')
profiles_df['Education'] = profiles_df['Education'].apply(lambda x: '\n'.join([f"{edu['School Name']}, {edu['Degree Name']}, {edu['Field of Study']}, {edu['Dates Attended']}" for edu in x]) if x else '')

# Save the DataFrame to a CSV file
profiles_df.to_csv('linkedin_profiles.csv', index=False, encoding='utf-8')

print("\nLinkedIn profile data has been successfully saved to linkedin_profiles.csv.")

