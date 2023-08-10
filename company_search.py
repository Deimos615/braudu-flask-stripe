import asyncio
import json
import time
import aiohttp 
import pandas as pd 
import requests,os
# api_key = os.environ.get('NEBULA_API_KEY')
api_key = 'asdfasdfasdf'
header_dic = {'Authorization': 'Bearer ' + api_key}

async def fetch_company_data(session,url):
    api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/company'
    params = {
        'url': url,
        'resolve_numeric_id': 'true',
        # 'categories': 'include',
        'funding_data': 'include',
        # 'extra': 'include',
        # 'exit_data': 'include',
        # 'acquisitions': 'include',
        'use_cache': 'if-recent',
    }
    async with session.get(api_endpoint,params=params, headers=header_dic) as response:
        response_json =  await response.json()
        if response.status  == 200:
            return response_json
        else:
            return None 
 
async def linkedin_company_search(session,nb_results=10,funding_raised=None,last_funding_round=None,industry=None,specialities=None,company_size=None,cities=None,country=None): 
    # print(f"Arguments passed to linkedin_company_search {nb_results,funding_raised,last_funding_round,specialities,company_size,country}")
    api_endpoint = 'https://nubela.co/proxycurl/api/search/company'
    if company_size != '':
        min,max = company_size.split('-')
    else :
        min,max = '',''
    if nb_results == '':
        nb_results= 10
    params = {
    'enrich_profiles': 'skip',
    'page_size': str(nb_results),
    'funding_raised_after': last_funding_round,
    'funding_amount_min': funding_raised,
    'description':f"(?i)({'|'.join(specialities)})",
    'employee_count_min': min,
    'employee_count_max': max,
    'industry': industry,
    'city': f"(?i)({'|'.join(cities)})",
    'country': country
    }
    if funding_raised == '':
        del params['funding_amount_min']
    if  last_funding_round == '':
        del params['funding_raised_after']
    if cities == ['']:
        del params['city']
    if company_size == '':
        del params['employee_count_min']
        del params['employee_count_max']
    if industry == '' or industry == None:
        del params['industry']
    print(f"Params passed to linkedin_company_search {params}")
    async with session.get(api_endpoint,params=params, headers=header_dic) as response:
        response_json =  await response.json()
        if response.status  == 200:
            return response_json
        else:
            return None 

async def process_company_search(nb_results=50,funding_raised=None,last_funding_round=None,industry=None,specialities=None,company_size=None,cities=None,country=None):
  # Extract required information
    start = time.time()
    async with aiohttp.ClientSession() as session:
        data = await linkedin_company_search(session,nb_results=nb_results,funding_raised=funding_raised,last_funding_round=last_funding_round,industry=industry,specialities=specialities.split(","),company_size=company_size,cities=cities.split(","),country=country)
        if data != None: 
            print(f"Time spent on searching {time.time()-start}")
        else :
            return [],0
        records = []
        tasks =[]
        for entry in data['results']:
            task = fetch_company_data(session, entry["linkedin_profile_url"])
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        for result in results:
            if result is not None:
                profile = process_company_profile(result)
                records.append(profile)
                
        print(f"Total time spent on digging companies {time.time()- start}")
        return records,data["total_result_count"]

def process_company_profile(profile):
    print("Processing company profile")
    funding_raised = 0 
    latest_funding_type = ''
    latest_funding_date = None
    for fund in profile.get('funding_data', []): 
      if fund['money_raised']:  
        funding_raised += fund['money_raised']
      announced_date = fund.get('announced_date')
      if announced_date:
          funding_date = pd.Timestamp(announced_date['year'], announced_date['month'], announced_date['day'])
          if latest_funding_date is None or funding_date > latest_funding_date:
              latest_funding_date = funding_date
              latest_funding_type = fund['funding_type']
    headquarters = profile.get('hq', {})
    if headquarters:
        location = f"{headquarters.get('city', '')}, {headquarters.get('state', '')}, {headquarters.get('country', '')}"
    else: 
        location = ''
    company_size = profile.get('company_size', '')
    if company_size:
        if company_size[1]:
            company_size = f"{company_size[0]}-{company_size[1]}"
        else:
            company_size = company_size[0]
    else:
        company_size = ''
    company_linkedin_url = "www.linkedin.com/company/" + profile.get('universal_name_id', '')
    company_name = profile.get('name', '')
    return {
              'Company name': f'{company_name}',
              'Company LinkedIn URL': f'https://{company_linkedin_url}',
              'Specialities': ', '.join(profile.get('specialities', [])[:3]),
              'Total funding raised in USD': funding_raised,
              'Type of latest funding round': latest_funding_type,
              'Number of employees on LinkedIn': str(profile.get('company_size_on_linkedin', '')).split(".")[0],
              'Total number of employees': company_size,
              "Headquarter’s location": location
          }
