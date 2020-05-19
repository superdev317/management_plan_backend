
from .models import ToDoList,Notification
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from django.utils.timezone import activate
import pytz
from django.utils.dateparse import parse_datetime
from .models import ToDoList,Notification
import time
from fcm_django.models import FCMDevice
import requests
import dwollav2
from accounts.models import BankAccounts
from projects.models import Transactions
import json

CLIENT_ID = 'i86COwfTm4xdSAYC71ZeZg55Cg3a8hULOEiXYUftAh783aaqWu'
CLIENT_SECRET_KEY = 'gk2qlNDrK33FkYLTMdJRD9o7EVZze67OhLS5KzRIIKnjcO54vm'
GRANT_TYPE = 'client_credentials'
DWOLLA_URL = 'https://sandbox.dwolla.com/oauth/v2/token'

response = requests.get('https://timezoneapi.io/api/ip')
data = response.json()

# freegeoip_response = requests.get('http://freegeoip.net/json')
# freegeoip_response_json = freegeoip_response.json()
# user_time_zone = freegeoip_response_json['time_zone']
user_time_zone = data['data']['timezone']['id']
tz = pytz.timezone(user_time_zone)

today = timezone.now()
day = today.date().today().strftime("%w")
date = today.date()
month = str(today.month)
# time = today.time()
today = today.astimezone(tz).replace(tzinfo=None)
time_now =  datetime.strftime(today, "%H:%M")


def get_notifications():
    queryset = ToDoList.objects.filter(is_complete=False)
    to_do_list_n = []
    week_list=[]
    month_list=[]

    for i in queryset:
        if i.remind == 'yearly':
            if i.start_on == date:
                for each in i.frequency_time.all():
                    each_str =  each.time.strftime("%H:%M")
                    if each_str == time_now:
                        to_do_list_n.append(i)

        if i.remind == 'daily':
            if i.start_on <= date:
                for each in i.frequency_time.all():
                    each_str = each.time.strftime("%H:%M")
                    if each_str == time_now:
                        to_do_list_n.append(i)

        if i.remind == 'weekly':
            if i.start_on <= date:
                for d in i.repeat_days:
                    week_list.append(d)
                if day in week_list:
                    for each in i.frequency_time.all():
                        each_str = each.time.strftime("%H:%M")
                        if each_str == time_now:
                            to_do_list_n.append(i)

        if i.remind == 'monthly':
            if i.start_on <= date:
                for m in i.repeat_months:
                    month_list.append(m)
                if month in month_list:
                    for each in i.frequency_time.all():
                        each_str = each.time.strftime("%H:%M")
                        if each_str == time_now:
                            to_do_list_n.append(i)

    for i in to_do_list_n:
        Notification.objects.create(to_do_list=i,title=i.task)

def delete_notification():
    delete_notifcation = []
    d = Notification.objects.all()
    for i in d:
        time_to_delete = timezone.now()+timedelta(days=1)
        time_to_delete = time_to_delete.strftime('%Y-%m-%d %H:%M')
        read_date = i.read_date.strftime('%Y-%m-%d %H:%M')
        if read_date == time_to_delete:
            delete_notifcation = Notification.objects.filter(id=i.id).delete()
    return delete_notifcation



def create_customer(data):
    request_customer_body = {
      'firstName': data['FirstName'],
      'lastName': data['LastName'],
      'email': data['email'],
      'type': 'personal',
      'address1':'sanpada',
      'city':'mumbai',
      'state':'IN',
      'postalCode':'11101',
      'dateOfBirth':'1970-01-01',
      'ssn':'1234'

    }
    # using dwolla library visit https://github.com/Dwolla/dwolla-v2-python
    client = dwollav2.Client(key = CLIENT_ID,
                             secret = CLIENT_SECRET_KEY,
                             environment = 'sandbox')

    app_token = client.Auth.client()
    print("aaaaaaaaaaaaaaaaaaaaaaa",app_token)

    try:
        #First we try to create customer
        customer = app_token.post('customers', request_customer_body)

        #customer = app_token.post "customers", request_customer_body
        customer_url = customer.headers['location']

        #update customer_url in our table
        update_customer_url = BankAccounts.objects.filter(user__email=data['email']).update(customer_url=customer_url)
    except:
        # if customer already exists we get a customer_url from our database
        customer_url = update_customer_url = BankAccounts.objects.filter(user__email=data['email']).values('customer_url')[0]
        customer_url = customer_url['customer_url']

    # Create a funding source for an account
    request_bank_body = {
    'routingNumber': data['routing_number'],
    'accountNumber': data['bank_account_no'],
    'bankAccountType':  data['account_type'],
    'name': data['bank_name']
    }

    #customer = app_token.post('funding-sources', request_bank_body)

    # Create a funding source for a customer
    # request_bank_body = {
    # 'routingNumber': data['routing_number'],
    # 'accountNumber': data['bank_account_no'],
    # 'bankAccountType':  data['account_type'],
    # 'name': data['FirstName'] +' '+ data['LastName']
    # }
 
    customer = app_token.post('%s/funding-sources' %customer_url, request_bank_body)
    funding_source_url = customer.headers['location']
    status = customer.status
    if status == 201:
        #update_funding_url = BankAccounts.objects.filter(user__email=data['email']).update(funding_source=funding_source_url)
        # Funding source verification (Micro-deposit verification)
        bank_micro_deposite = app_token.post('%s/micro-deposits' % funding_source_url)
        if bank_micro_deposite.status == 201:
            
            # To Verify micro-deposits
            request_body = {
                "amount1": {
                    "value": "0.03",
                    "currency": "USD"
                },
                "amount2": {
                    "value": "0.09",
                    "currency": "USD"
                }
            }

            bank_verify = app_token.post('%s/micro-deposits' % funding_source_url, request_body)
            status = bank_verify.status
            data = {
                'status':status,
                'funding_source_url':funding_source_url,
            }
            return data

def create_transactions(data):

    if data['bank_account']:
        bank_obj = BankAccounts.objects.get(id=data['bank_account'].id)

    if data['mode'] == 'deposite':
        source = 'https://api-sandbox.dwolla.com/funding-sources/4bc5c63f-767e-4e53-a820-601aef335349'  #superhero (merchant account)
        destination = 'https://api-sandbox.dwolla.com/funding-sources/b6ad21b5-2709-45bd-a1be-79e971cf808c' #Balance (wallet)
        
    elif data['mode'] == 'withdrawal':
        source = 'https://api-sandbox.dwolla.com/funding-sources/b6ad21b5-2709-45bd-a1be-79e971cf808c' #Balance (wallet)
        destination = bank_obj.funding_source #customer bank

    request_body = {
              '_links': {
                'source': {
                  'href': source
                },
                'destination': {
                  'href': destination
                }
              },
              'amount': {
                'currency': 'USD',
                'value': int(data['amount'].amount)
              }  
        }

    client = dwollav2.Client(key = CLIENT_ID,
                             secret = CLIENT_SECRET_KEY,
                             environment = 'sandbox')

    app_token = client.Auth.client()

    transfer = app_token.post('transfers', request_body)
    transfer_url= transfer.headers['location'] # => 'https://api.dwolla.com/transfers/74c9129b-d14a-e511-80da-0aa34a9b2388' 

    transfer1 = app_token.get(transfer_url)
    status = transfer1.body['status']

    return status                                                                                