import boto3
import datetime
import json
import pandas as pd
import pendulum
import requests
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from datetime import datetime

# UPDATE THIS WITH THE REGION THAT YOUR SSM PARAMETERS ARE IN
REGION =  '' 

# UPDATE THESE VALUES FROM THE AWS IAM ROLE 
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

# DO NOT CHANGE THESE
BROWSER = 'Chrome'
BROWSER_VERSION = '88.0.4324.150'
DRIVER_VERSION = '88.0.4324.96'

# WE CAN DEAL WITH THIS LATER
YEAR = '2023'

"""
THIS WILL BE THE NAME OF YOUR GROUPME BOT. 
IT SHOULD ALSO BE IN THE NAME OF YOUR PARAMETERS SO YOU CAN HAVE MULTIPLE BOTS
"""
GROUPME_BOT_NAME = 'dev' #os.environ.get('GROUPME_BOT_NAME') # string


def get_parameters():
   """
   GET PARAMETERS FROM AWS AND CREATE VARIABLES FOR SCRIPT
   """
   client = boto3.client(
      'ssm', 
      region_name=REGION, 
      aws_access_key_id=AWS_ACCESS_KEY_ID,
      aws_secret_access_key=AWS_SECRET_ACCESS_KEY
   )

   parameters = client.get_parameters_by_path(Path=f'/{GROUPME_BOT_NAME}/')
   params_dict = {}

   # LOOP THROUGH PARAMS TO CREATE DICTIONARY
   for parameter in parameters['Parameters']:
      params_dict[parameter['Name']] = parameter['Value']

   # READ AND DECRYPT THE BOT_ID
   params_dict[f'/{GROUPME_BOT_NAME}/bot_id'] = client.get_parameter(Name=f'/{GROUPME_BOT_NAME}/bot_id', WithDecryption=True)['Parameter']['Value']

   return params_dict



parameters = get_parameters()
print(parameters)

BOT_ID = parameters[f'/{GROUPME_BOT_NAME}/bot_id'] # string
COURSES = parameters[f'/{GROUPME_BOT_NAME}/courses'] # array[string] ex. ['course name','course url']
MIN_TIME = parameters[f'/{GROUPME_BOT_NAME}/min_time'] # string '8:00PM'
MAX_TIME = parameters[f'/{GROUPME_BOT_NAME}/max_time'] # string '12:00PM'
HOLES = parameters[f'/{GROUPME_BOT_NAME}/holes'] # string ex. 18
# NUMBER_OF_PLAYERS = parameters[f'/{GROUPME_BOT_NAME}/number_of_players'] # string ex. 2-4
DAYS = parameters[f'/{GROUPME_BOT_NAME}/days'] # array[string] ex. ['SATURDAY','SUNDAY']

"""
DO NOT CHANGE. SET TO WORK WITH DOCKER CONTAINER
"""
def set_chrome_options() -> None:
   """Sets chrome options for Selenium.
   Chrome options for headless browser is enabled.
   """
   chrome_options = ChromeOptions()
   chrome_options.add_argument("--headless")
   chrome_options.add_argument("--no-sandbox")
   chrome_options.add_argument("--disable-dev-shm-usage")
   chrome_prefs = {}
   chrome_options.experimental_options["prefs"] = chrome_prefs
   chrome_prefs["profile.default_content_settings"] = {"images": 2}
   return chrome_options

chrome_options = set_chrome_options()
driver = webdriver.Chrome(options=chrome_options)


def connect_to_url(url):
	return driver.get(url)


def navigate_to_course_homepage(url):
	connect_to_url(url)


def get_dates_between(golf_date_string, current_date_string):
   """
   CALCULATES THE NUMBER OF DAYS BETWEEN THE CURRENT DAY AND THE DAY YOU WANT TEE TIMES FOR
   """
   golf_date = datetime.strptime(golf_date_string, '%Y%m%d').date()
   current_date = datetime.strptime(f'{current_date_string}, {YEAR}', '%a, %b %d, %Y').date()
   n_days = (golf_date - current_date).days
   print(f"Number of days: {n_days}")

   return n_days


def click_next_day():
   """
   CLICKS THE NEXT DAY BUTTON
   """
   driver.find_element(By.ID, 'nextDay').find_element(By.TAG_NAME, 'div').click()
   print(f"Current date: {driver.find_element(By.CLASS_NAME, 'tot-date-picker').text}")
	

def click_previous_day():
   """
   CLICKS THE PREVIOUS DAY BUTTON
   """
   driver.find_element(By.ID, 'previousDay').find_element(By.TAG_NAME, 'div').click()
   print(f"Current date: {driver.find_element(By.CLASS_NAME, 'tot-date-picker').text}")


def update_date(golf_date, current_date):    
   """
   NAVIGATES TO THE DATE YOU WANT TO GET TEE TIMES FOR
   """
   # GET NUMBER OF DAYS TO NAVIGATE TO
   n_days = get_dates_between(golf_date, current_date)

   # UPDATE FLAG TO MOVE FORWARD OR BACK IN TIME
   if n_days < 0:
      click_previous = True
   elif n_days > 0:
      click_previous = False
   else:
      print(f'We are on golf date: {golf_date}')
	
   # EITHER CLICK FORWARD OR BACKWARD IN TIME
   for i in range(abs(n_days)):
      if n_days < 0:
         click_previous_day() 
      elif n_days > 0:
         click_next_day() 
      else:
         print(f'We are on golf date: {golf_date}')
      sleep(1)
	 

def get_times():
   """
   GET THE TEE TIMES ARRAY 
   """
   search_results = driver.find_elements(By.CLASS_NAME, 'search-results')
   search_results

   time_array = []
   for time in search_results[1].find_elements(By.CLASS_NAME, 'promoted-campaign-wrapper'):
      time_dict = {}
      time_dict['time'] = time.find_element(By.TAG_NAME, 'time').text
      time_dict['price'] = '${:,.2f}'.format(int(time.find_element(By.TAG_NAME, 'p').text[1:])/100)
      tt_detail = time.find_element(By.CLASS_NAME, 'tt-detail')
      time_dict['holes'] = tt_detail.find_elements(By.TAG_NAME, 'span')[0].text
      time_dict['number of players'] = tt_detail.find_elements(By.TAG_NAME, 'span')[2].text
      
      time_array.append(time_dict)
      
   return time_array
         
      
def build_body_text(course_name, times, date):   
   """
   FILTER DATAFRAME BASED ON PARAMS
   CREATE OUTPUT MESSAGE

   (SHOULD SPLIT THIS)
   """
   df = pd.DataFrame(times)
   df = df[df['number of players'].isin(['1-4', '2-4', '4'])]
   df = df[df['holes'] == HOLES]
   df['time_real'] = pd.to_datetime(df['time'], format='%I:%M%p').dt.time
   df = df[df['time_real'] > datetime.strptime(MIN_TIME, '%I:%M%p').time()]
   df = df[df['time_real'] < datetime.strptime(MAX_TIME, '%I:%M%p').time()]
   df.drop('time_real', axis=1, inplace=True)
   df.drop('number of players', axis=1, inplace=True)
   df.drop('holes', axis=1, inplace=True)
   df.set_index('time', inplace=True)
   if len(df) == 0:
      print('No data')
    
      return None

   if len(df) > 0:
      string_df = df.to_string()
      text = f"{course_name} on {datetime.strptime(date, '%Y%m%d').strftime('%A (%m/%d)')} \n{string_df}"

      return text

def send_times(text):
   """
   SEND TIMES TO GROUPME
   """
   print(text)
   body = {
      'text': text,
      'bot_id': BOT_ID
   }
   print(body)

   body = json.dumps(body)

   response = requests.post(
      url='https://api.groupme.com/v3/bots/post',
      data=body
   )
   print(response.status_code)
   print(response.text)


def get_course_dict(course_list):
   """
   PARSE COURSE PARAMS FOR PROCESS
   """
   if len(course_list)%2 != 0:
      print('need an even length')
   course_dict_array = []  
   for item in range(0,len(course_list),2):
      course_dict = {}
      course_dict['course'] = course_list[item]
      course_dict['url'] = course_list[item+1]
      course_dict_array.append(course_dict)

   return course_dict_array



def get_dates(days):
   """
   PASS THE DATES WE WANT BASED ON INPUT PARAMS
   """
   if not days:
      print('Need to provide days')
      return None

   dates = []

   if 'SUNDAY' in days:
      dates.append(pendulum.now().next(pendulum.SUNDAY).strftime('%Y%m%d'))
   if 'MONDAY' in days:
      dates.append(pendulum.now().next(pendulum.MONDAY).strftime('%Y%m%d'))
   if 'TUESDAY' in days:
      dates.append(pendulum.now().next(pendulum.TUESDAY).strftime('%Y%m%d'))
   if 'WEDNESDAY' in days:
      dates.append(pendulum.now().next(pendulum.WEDNESDAY).strftime('%Y%m%d'))
   if 'THURSDAY' in days:
      dates.append(pendulum.now().next(pendulum.THURSDAY).strftime('%Y%m%d'))
   if 'FRIDAY' in days:
      dates.append(pendulum.now().next(pendulum.FRIDAY).strftime('%Y%m%d'))
   if 'SATURDAY' in days:
      dates.append(pendulum.now().next(pendulum.SATURDAY).strftime('%Y%m%d'))
   
   return dates


def get_courses_date_data(courses, dates):
   """
   RUN APP FOR A COURSE AND DATE
   """
   text = None
   for date in dates:
      for course in courses:
         course['golf_date'] = date
         navigate_to_course_homepage(course['url'])

         current_date = driver.find_element(By.CLASS_NAME, 'tot-date-picker').text

         update_date(course['golf_date'], current_date)

         times = get_times()

         if times:
            text = build_body_text(course['course'], times, course['golf_date'])
            print(text)
            send_times(text)

	# return text


def lambda_handler(event, context):
   print(DAYS)
   print(DAYS.split(','))
   dates = get_dates(DAYS.split(','))
   print('dates: ', dates)
   courses = get_course_dict(COURSES.split(','))
   print('courses: ', courses)
   response = get_courses_date_data(courses, dates)
   


if __name__ == '__main__':
   lambda_handler(None, None)