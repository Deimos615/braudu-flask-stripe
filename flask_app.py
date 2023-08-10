from flask import Flask, render_template, request,session,redirect, url_for, jsonify
import json,os,sys
import pandas as pd
from flask_session import Session  # pip install Flask-Session
from company_search import * 
import stripe
import boto3
from datetime import datetime

from  braudu_flagged import * 

from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import hashlib

stripe_keys = {
    # "secret_key": os.environ["STRIPE_SECRET_KEY"],
    # "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "secret_key": 'sk_test_51NbnjSJkkJ9MkzC7vwm4p5FlNVvANaoLui9kEKXPJ2LOpVQj7yIAe2lETJmHYKfrVA7NqRSoaNFlaMukshrASeLb0073o4VC2b',
    "publishable_key": 'pk_test_51NbnjSJkkJ9MkzC7QuzO4VnGhn4vdAw7qJUiChXbEXooTwqtQHLrG37WQRVTuduholrrJPXt3HAgZamEHadkrvlO007lT8SNzt',
    # "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"]
}

google_credits = 10
openai_credits = 10
linkedin_credits = 10

stripe.api_key = stripe_keys['secret_key']


table_columns = ["Score","Company name","Full name",'Job title',"Emails","Phone numbers","Total number of employees","Headquarter’s location"]
input_file = directory+  "/files/input_data.xlsx"

input_columns = ["company_name","company_linkedin_profile","company_size","company_location"]
output_columns = ['score','company_name', 'company_linkedin_profile', 'full_name', 'job_title',
       'person_linkedin_profile',"emails","phone_numbers",'company_size',
       'company_location']


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = 'your secret key'
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'python_search_db'
 
mysql = MySQL(app)


@app.route('/')
def index():
    if session.get('loggedin', False):
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sha1_hash = hashlib.sha1()
        sha1_hash.update(password.encode('utf-8'))
        hashed_password = sha1_hash.hexdigest()
        cursor.execute('SELECT * FROM users WHERE email = % s AND password = % s', (email, hashed_password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['email'] = account['email']
            session['token'] = account['token']
            session['user'] = account
            msg = 'Logged in successfully !'
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect email / password !'
    return render_template('login.html', msg = msg, current_user=session.get('user', {}))
 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    session.pop('token', None)
    session.pop('user', None)
    return redirect(url_for('login'))
 
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and 'email' in request.form :
        email = request.form['email']
        password = request.form['password']
        username = request.form['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', email):
            msg = 'email must contain only characters and numbers !'
        elif not email or not password or not username:
            msg = 'Please fill out the form !'
        else:
            sha1_hash = hashlib.sha1()
            sha1_hash.update(password.encode('utf-8'))
            hashed_password = sha1_hash.hexdigest()
            token_hash = hashlib.sha1()
            token_hash.update(email.encode('utf-8'))
            hashed_token = token_hash.hexdigest()
            cursor.execute('INSERT INTO users (email, password, username, token, created_at, updated_at) VALUES (% s, % s, % s, % s, % s, % s)', (email, hashed_password, username, hashed_token, str(datetime.now())[0:19], str(datetime.now())[0:19]))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg, current_user=session.get('user', {}))

@app.route('/home')
def home():
    loggedin = session.get('loggedin', False)
    print(loggedin)
    if loggedin:
        token = session.get('token', '')
        return render_template('main.html', token=token, current_user=session.get('user', {}))
    else:
        return redirect(url_for('login'))
    
@app.route('/charge', methods=['POST'])
def charge():
    amount = 100  # Amount in cents
    try:
        email = session.get('email')
        # customer = stripe.Customer.create(
        #     email=email,
        #     source=request.form['stripeToken']
        # )
        # print('customer.....', customer)
        # Create a charge using the Stripe API
        
        charge = stripe.Charge.create(
            # customer=customer['id'],
            amount=amount * 100,
            currency='usd',
            description='user: "' + email + '" charged $' + str(amount) + ' at ' + str(datetime.now()),
            source=request.form['stripeToken']
        )
        session['user']['credits'] = session['user']['credits'] + amount
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET paid = paid + % s, credits = credits + % s WHERE email = % s', (amount, amount, email))
        cursor.execute('INSERT INTO payment_logs (email, charge_id, created_at, updated_at) VALUES (% s, % s, % s, % s)', (email, charge.id, str(datetime.now())[0:19], str(datetime.now())[0:19]))
        mysql.connection.commit()
        return render_template('main.html', current_user=session.get('user', {}))
    except stripe.error.CardError as e:
        return render_template('payment.html', key=stripe_keys['publishable_key'], current_user=session.get('user', {}))
    
@app.route('/person', methods=['GET', 'POST'])
def person():
    company_results = session.get('company_results', None)
    use_synonym_is_active= client.is_enabled("use-job-title-synonyms")
    if company_results is not None:
        data = pd.DataFrame(company_results)
    else:
        data = pd.read_excel(input_file) 
    if request.method == 'POST':
        try:
            use_credits = int(google_credits) + int(openai_credits) + int(linkedin_credits)
            email = session['user']['email']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE email = % s', (email, ))
            account = cursor.fetchone()
            if int(account['credits']) < int(use_credits):
                return render_template('company.html', credits_error=True, msg="There are no available credits", credits=account['credits'], current_user=session.get('user', {}))
            else:
                company_results = session.get('company_results', None)
                if company_results is not None:
                    data = pd.DataFrame(company_results)
                else:
                    data = pd.read_excel(input_file)            
                    job_title = request.form['job_title']
                    results_per_company = int(request.form['results_per_company'])
                    use_synonyms = 'use_job_title_synonyms' in request.form
                    #Record start time 
                    start = time.time()
                    # Process data asynchronously
                    output_df = process_data(data,job_title,results_per_company,use_synonyms)
                    if client.is_enabled("display-run-time-persons-page"): 
                        time_spent = f"in {round(time.time()-start,2)} seconds"
                    else:
                        time_spent = ""            
                    result = format_output_person_page(output_df)
                    return render_template('index.html', result=result,job_title=job_title,total_rows=len(output_df),time_spent=time_spent,use_job_title_synonyms=use_synonyms,results_per_company=results_per_company,synonyms_filter_active=use_synonym_is_active, current_user=session.get('user', {}))
        except Exception as e:
            return render_template('index.html', result='error',synonyms_filter_active=use_synonym_is_active,error_message=str(e), current_user=session.get('user', {}))
    else:
        data.columns = input_columns
        data.drop(columns=["company_size","company_location"], inplace=True)
        data = hyperlink(data,"company_name","company_linkedin_profile")
        data.drop(columns=["company_linkedin_profile"], inplace=True)
        data.columns = ["Customer List"]
        html_table = data.to_html(index=False,escape=False)
        return render_template('index.html', result=html_table,results_per_company=3,synonyms_filter_active=use_synonym_is_active, current_user=session.get('user', {}))

@app.route('/payment', methods=['GET'])
def create_checkout_session():
    token = request.args.get('token')
    if token:
        if not session.get('loggedin', False):
            return redirect(url_for('login'))
        elif session['user']['token'] != token:
            return redirect(url_for('login'))
        elif session['user']['token'] == token:
            return render_template('payment.html',key=stripe_keys['publishable_key'], current_user=session.get('user', {}))
    else:
        return redirect(url_for('login'))

@app.route('/company', methods=['GET','POST'])
def company():
    industries_active = client.is_enabled("industry-filter")
    if industries_active:
        industries = get_indutries()
    else:
        industries = []
    if request.method == 'GET':
        return render_template('company.html',company_size="",industries_list=industries,industries_active=industries_active, current_user=session.get('user', {}))
    elif request.method == 'POST':
        use_credits = int(google_credits) + int(openai_credits) + int(linkedin_credits)
        email = session['user']['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if int(account['credits']) < int(use_credits):
            return render_template('company.html', credits_error=True, msg="There are no available credits", credits=account['credits'], current_user=session.get('user', {}))
        else:
            session['user']['credits'] = int(session['user']['credits']) - int(use_credits)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE users SET credits = credits - % s WHERE email = % s', (use_credits, session['email']))
            mysql.connection.commit()
            action = request.form.get('action')
            specialities = request.form.get('specialities')
            company_size = request.form.get('company_size')
            funding_raised = request.form.get('funding_raised')
            last_funding_round = request.form.get('last_funding_round')
            cities = request.form.get('cities')
            country = request.form.get('country')
            industry = request.form.get('industry')
            nb_results = request.form.get('number_results')
            if action == 'start':
                return run_company_search(industry,specialities,company_size,funding_raised,last_funding_round,cities,country,nb_results,industries_list=industries,industries_active=industries_active)
            elif action == 'export':
                company_results = session.get('company_results', None)
                if company_results is not None:
                    return redirect(url_for('person'))
                else:
                    return render_template('company.html', data="error",industries_list=industries,industries_active=industries_active, current_user=session.get('user', {}))

def run_company_search(industry,specialities,company_size,funding_raised,last_funding_round,cities,country,nb_results,industries_list,industries_active):
    start = time.time()
    # checkCreditResult = 
    records,total_results_found = asyncio.run( process_company_search(nb_results=nb_results,funding_raised=funding_raised,last_funding_round=last_funding_round,industry=industry,specialities=specialities,company_size=company_size,cities=cities,country=country))
    if client.is_enabled("display-run-time-companies-page"): 
        time_spent = f"in {round(time.time()-start,2)} seconds"
    else:
        time_spent = ""            
    if len(records) > 0:
        df = pd.DataFrame(records)  
        session['company_results'] = (format_input(df)).to_dict('records')
        data_html = format_output_companies_page(df)

    else :
        data_html= "No results found"
    return render_template('company.html', data=data_html,industry=industry,
        specialities=specialities, company_size=company_size,
        funding_raised=funding_raised, last_funding_round=last_funding_round,
        cities=cities, country=country, number_results=nb_results,
        nb_results_displayed=len(records),time_spent=time_spent,industries_list=industries_list,industries_active=industries_active, current_user=session.get('user', {}))

def format_output_person_page(output_df):
    output_df = output_df.sort_values(by=output_df.columns[0], key=lambda x: x.str.lower())
    output_df = hyperlink(output_df,"full_name","person_linkedin_profile")
    output_df = hyperlink(output_df,"company_name","company_linkedin_profile")
    output_df = output_df[output_columns] #reorder columns
    output_df.drop(columns=["company_linkedin_profile","person_linkedin_profile"], inplace=True)
    output_df.columns = table_columns
    if not client.is_enabled("get-person-email"): 
        output_df= output_df.drop(columns=["Emails"])
    if not client.is_enabled("get-person-phone-numbers"): 
        output_df= output_df.drop(columns=["Phone numbers"])
    return output_df.to_html(index=False, escape=False)


def format_output_companies_page(df):
    df = hyperlink(df,"Company name","Company LinkedIn URL")
    df =df.drop(columns=["Company LinkedIn URL"])
    df['Total funding raised in USD'] = df['Total funding raised in USD'].apply(lambda x: "${:,.0f}".format(x))
    return df.to_html(index=False,escape=False)
     
def hyperlink(df,column_name,column_value):
    df[column_name] = df.apply(lambda row: '<a href="{}" target="_blank">{}</a>'.format(row[column_value], row[column_name]), axis=1)
    return df

def format_input(df):
    df = df.drop(columns=["Specialities",'Total funding raised in USD','Type of latest funding round',"Number of employees on LinkedIn"])
    df.columns = input_columns
    return df
    
    
def get_indutries():
    df = pd.read_excel("files/Distinct_industries.xlsx")
    ind_list = [""]+df["industry"].tolist() 
    return ind_list
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5001)
