
import dwollav2
from django.views.decorators.csrf import csrf_protect, csrf_exempt
import json
from django.http import HttpResponse

# Navigate to https://www.dwolla.com/applications (production) or https://dashboard-sandbox.dwolla.com/applications (Sandbox) for your application key and secret.
@csrf_exempt
def abc(request):
	app_key = 'r3FaC8xRI3b2HrKavhHNz0ebpiSTPxMjMAzDIW1iXL4Y4hqoR0'
	app_secret = 'ZPaDoMwOMXDj8TGU06vKpXBU1HDhG6GNCEi2FHWiiEnVCHzUGr'
	client = dwollav2.Client(key = app_key,
	                         secret = app_secret,
	                         environment = 'sandbox') # optional - defaults to production

	app_token = client.Auth.client()


	customers = app_token.get('customers', {'limit': 10})
	
	######################## Create Customer start########################################
	# request_body = {
	# 	'firstName': 'Test',
	# 	'lastName': 'Merchant2',
	# 	'email': 'merchant@nomail.net',
	# 	'ipAddress': '99.99.99.99'
	# }

	# # Using dwollav2 - https://github.com/Dwolla/dwolla-v2-python (Recommended)
	# customer = app_token.post('customers', request_body)
	# customer.headers['location'] # => 'https://api-sandbox.dwolla.com/customers/c7f300c0-f1ef-4151-9bbe-005005aa3747'

	######################## Create Customer end########################################
	
	######################## Create Customer Funding sources start ########################################
	# customer_url = "https://api-sandbox.dwolla.com/customers/9607d166-f951-481f-b6ce-8c7e5e326b2b"
	# request_body = {
	# 	'routingNumber': '222222226',
	# 	'accountNumber': '123456777',
	# 	'bankAccountType': 'checking',
	# 	'name': 'Jane Merchant1 - Checking 678988'
	# }

	# # Using dwollav2 - https://github.com/Dwolla/dwolla-v2-python (Recommended)
	# customer = app_token.post('%s/funding-sources' % customer_url, request_body)
	# customer.headers['location'] # => 'https://api-sandbox.dwolla.com/funding-sources/375c6781-2a17-476c-84f7-db7d2f6ffb31'

	# print ("ssssssssssssssssssssssssssssssssssssssssssss", customer.headers['location'])
	######################## Create Customer Funding sources end ########################################


	transfer_request = {
		'_links': {
			'source': {
				'href': 'https://api-sandbox.dwolla.com/funding-sources/7f5b2b5b-5331-4f81-9c64-bdcad1fca450'
			},
			'destination': {
				'href': 'https://api-sandbox.dwolla.com/customers/ccbc7837-b90c-4cfb-af5e-38f1af3dc4b5'
				# 'Email': 'mailto:testmerchant@nomail.net'
			}
		},
		'amount': {
			'currency': 'USD',
			'value': '10.00'
		},
		'metadata': {
			'customerId': 'ccbc7837-b90c-4cfb-af5e-38f1af3dc4b5',
			'notes': 'For work completed on Sept. 1, 2015'
		}
	}

	# Using dwollav2 - https://github.com/Dwolla/dwolla-v2-python (Recommended)
	transfer = app_token.post('transfers', transfer_request)
	transfer.headers['location'] # => 'https://api.dwolla.com/transfers/d76265cd-0951-e511-80da-0aa34a9b2388'

	print ("ssssssssssssssssssssssssssssssssssssssssssss", transfer.headers['location'])
	return HttpResponse(transfer.headers['location'], content_type="application/json")
