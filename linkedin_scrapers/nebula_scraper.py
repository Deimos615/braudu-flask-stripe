import json,requests
import time,os,re
import pandas as pd

# api_key = os.environ.get('NEBULA_API_KEY')
api_key = 'asdfasdfasdf'
header_dic = {'Authorization': 'Bearer ' + api_key}

def extract_linkedin_ids(url):
    if  'company' in  url :
        company_pattern = r"(?<=linkedin\.com\/company\/)([^\/\?\s]+)"
        company_match = re.search(company_pattern, url)
        company_id = company_match.group(0) if company_match else None
        return company_id
    else : 
        person_pattern = r"(?<=linkedin\.com\/in\/)([^\/\?\s]+)"
        person_match = re.search(person_pattern, url)
        person_id = person_match.group(0) if person_match else None
        return person_id
    
def scrape_profile(profile):
    api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'
    params = {
        'url': profile,
        'use_cache': 'if-recent'
        
    }
    response = requests.get(api_endpoint,params=params, headers=header_dic)
    
    if response.status_code  == 200:
        response_json =   response.json()
        return response_json
    else:
        return None 

def scrape_person_email(profile):
    api_endpoint = 'https://nubela.co/proxycurl/api/contact-api/personal-email'
    params = {
        'linkedin_profile_url': profile,
    }
    response = requests.get(api_endpoint,
                            params=params,
                            headers=header_dic)
    if response.status_code  == 200:
        response_json =   response.json()
        return " , ".join(response_json['emails'])
    else:
        return None 

def scrape_phone_number(profile):
    api_endpoint = 'https://nubela.co/proxycurl/api/contact-api/personal-contact'
    params = {
        'linkedin_profile_url': profile,
        'page_size': '0',
    }
    response = requests.get(api_endpoint,
                            params=params,
                            headers=header_dic)
    if response.status_code  == 200:
        response_json =   response.json()
        return " , ".join(response_json['numbers'])
    else:
        return None