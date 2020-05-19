from .models import ProjectBackerFund, Transactions, ProjectBackerLaunch, Project, UserCompanyShares, FundInterestPay
from .serializers import TransactionsSerializer
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from django.http import HttpResponse
import json
from dateutil.relativedelta import relativedelta


def get_fund_transactions():
    queryset1 = ProjectBackerFund.objects.filter(fund__fund__id__in=[1,4],fund__due_by__lte=date.today(),is_closed=False)
    queryset2 = ProjectBackerLaunch.objects.filter(project_launch__due_date__lte=date.today(),is_closed=False)

    for i in queryset1:
        amount = i.quantity * i.fund.price_security.amount
        data=[{
                "remark": "Project Fund",
                "mode": "withdrawal",
                "status": "success",
                "amount":{"amount":amount,"currency":"USD"},
                "user": 1
            },
            {
                "remark": "Project Fund",
                "mode": "deposite",
                "status": "success",
                "amount":{"amount":amount,"currency":"USD"},
                "user": i.fund.owner.id
            }
        ]

        s = TransactionsSerializer(data=data, many=True)
        s.is_valid(raise_exception=True)
        s.save(project=i.fund.project)
        i.is_closed=True
        i.save()

    for i in queryset2:
        amount = i.quantity * i.project_launch.price_per_share.amount
        data=[{
                "remark": "Project Launch",
                "mode": "withdrawal",
                "status": "success",
                "amount":{"amount":amount,"currency":"USD"},
                "user": 1
            },
            {
                "remark": "Project Launch",
                "mode": "deposite",
                "status": "success",
                "amount":{"amount":amount,"currency":"USD"},
                "user": i.project_launch.project.owner.id
            }
        ]

        s = TransactionsSerializer(data=data, many=True)
        s.is_valid(raise_exception=True)
        s.save(project=i.project_launch.project)
        i.is_closed=True
        i.save()
        
        shares, created = UserCompanyShares.objects.update_or_create(
            user=i.backer,
            project=i.project_launch.project,
        )  
        if i.project_launch.launch.id == 2:
            shares.isx_shares += i.quantity
            shares.save()   
        elif i.project_launch.launch.id == 3:
            shares.lsx_shares += i.quantity
            shares.save()   

    return #HttpResponse(json.dumps({"message":"success"}), content_type="application/json")

def project_registration():
    """
    Endpoint to register project on blockchain
    """
    from web3 import Web3
    from solc import compile_source
    from web3.contract import ConciseContract
    from web3.middleware import geth_poa_middleware

    projects = Project.objects.filter(is_registered=True, having_blockchain_entry=False)

    result =[]
    if projects:
        abi = [
                {
                    "anonymous": False,
                    "inputs": [
                        {
                            "indexed": False,
                            "name": "project_Title",
                            "type": "string"
                        },
                        {
                            "indexed": False,
                            "name": "project_Stage",
                            "type": "string"
                        },
                        {
                            "indexed": False,
                            "name": "ownerId",
                            "type": "uint256"
                        },
                        {
                            "indexed": False,
                            "name": "ownerName",
                            "type": "string"
                        },
                        {
                            "indexed": False,
                            "name": "status",
                            "type": "string"
                        },
                        {
                            "indexed": False,
                            "name": "registration_type",
                            "type": "string"
                        },
                        {
                            "indexed": False,
                            "name": "package",
                            "type": "string"
                        }
                    ],
                    "name": "LogRecord",
                    "type": "event"
                },
                {
                    "constant": False,
                    "inputs": [
                        {
                            "name": "_projectId",
                            "type": "uint256"
                        },
                        {
                            "name": "_project_Title",
                            "type": "string"
                        },
                        {
                            "name": "_project_Stage",
                            "type": "string"
                        },
                        {
                            "name": "_ownerId",
                            "type": "uint256"
                        },
                        {
                            "name": "_ownerName",
                            "type": "string"
                        },
                        {
                            "name": "_status",
                            "type": "string"
                        },
                        {
                            "name": "_registration_type",
                            "type": "string"
                        },
                        {
                            "name": "_package",
                            "type": "string"
                        }
                    ],
                    "name": "addProjectRgistrationDetails",
                    "outputs": [
                        {
                            "name": "",
                            "type": "bool"
                        }
                    ],
                    "payable": False,
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [
                        {
                            "name": "_projectId",
                            "type": "uint256"
                        }
                    ],
                    "name": "getProjectDetailsById",
                    "outputs": [
                        {
                            "name": "",
                            "type": "string"
                        },
                        {
                            "name": "",
                            "type": "string"
                        },
                        {
                            "name": "",
                            "type": "uint256"
                        },
                        {
                            "name": "",
                            "type": "string"
                        },
                        {
                            "name": "",
                            "type": "string"
                        },
                        {
                            "name": "",
                            "type": "string"
                        },
                        {
                            "name": "",
                            "type": "string"
                        }
                    ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
                }
            ]

        web3 = Web3(Web3.HTTPProvider("http://40.76.72.222:8501"))
        web3.middleware_stack.inject(geth_poa_middleware, layer=0)
        web3.eth.defaultAccount = web3.eth.accounts[0]
        address = Web3.toChecksumAddress("0xcd2529f401b59ed8bd9cb6beef6186431fa2257e")
        contract = web3.eth.contract(address=address,abi=abi)
        
        for i in projects:
            res = contract.functions.addProjectRgistrationDetails(i.id,i.title,i.stage,i.owner.id,i.owner.first_name,i.status,i.registration_type.title,i.package.title).transact()
            tx_receipt = web3.eth.waitForTransactionReceipt(res)

            if tx_receipt.get('status') == 1:
                i.having_blockchain_entry = True

            i.transaction_hash = tx_receipt.get('transactionHash').hex()
            i.block_number = tx_receipt.get('blockNumber')
            i.save()
   
    return

def create_interest_entries():
    queryset = ProjectBackerFund.objects.filter(fund__fund__id__in=[3,5],is_closed=False)

    for i in queryset:
        from_date = None
        
        if i.next_interest_payable_date:
            if i.next_interest_payable_date <= date.today():
                amount_to_pay = round((i.sanction_amount.amount * i.interest_rate) / 100)

                if i.payment_type == "monthly":
                    from_date = i.next_interest_payable_date - relativedelta(months=1)
                    i.next_interest_payable_date = i.next_interest_payable_date + relativedelta(months=1)
                    i.save()
                elif i.payment_type == "quarterly":
                    from_date = i.next_interest_payable_date - relativedelta(months=3)
                    i.next_interest_payable_date = i.next_interest_payable_date + relativedelta(months=3)
                    i.save()
                elif i.payment_type == "yearly":
                    from_date = i.next_interest_payable_date - relativedelta(months=12)
                    i.next_interest_payable_date = i.next_interest_payable_date + relativedelta(months=12)
                    i.save()
                FundInterestPay.objects.create(
                    backer_fund=i,
                    from_date=from_date,
                    to_date=i.next_interest_payable_date,
                    amount_to_pay=amount_to_pay,
                    interest_rate=i.interest_rate,
                )  


