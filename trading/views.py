from django.shortcuts import render

from .models import Bid, Ask, OrderBook
from projects.models import Project, Transactions, UserCompanyShares
from projects.serializers import TransactionsSerializer
from django.http import HttpResponse
import json

def get_user_share(user,project):
	obj, created = UserCompanyShares.objects.get_or_create(user=user,project=project )
	return obj

def mapping(request):
	projects = Project.objects.all()
	for project in projects:
		if project.project_launch.first():
			bid_requests=[]
			limit_ask_requests=[]
			market_ask_requests=[]

			if project.project_launch.first().launch.id == 2:
				bid_requests = Bid.objects.filter(is_closed=False, project=project, exchange_type="isx").order_by('id')
				limit_ask_requests = Ask.objects.filter(is_closed=False, project=project, order_type="limit", exchange_type="isx").order_by('id')
				market_ask_requests = Ask.objects.filter(is_closed=False, project=project,order_type="market", exchange_type="isx").order_by('id')
			elif project.project_launch.first().launch.id == 3:
				bid_requests = Bid.objects.filter(is_closed=False, project=project, exchange_type="lsx").order_by('id')
				limit_ask_requests = Ask.objects.filter(is_closed=False, project=project,order_type="limit", exchange_type="lsx").order_by('id')
				market_ask_requests = Ask.objects.filter(is_closed=False, project=project,order_type="market", exchange_type="lsx").order_by('id')

			limit_ask = list(limit_ask_requests)
			market_ask = list(market_ask_requests)

			final_solution = []
			for i in bid_requests:
				bidder_share_obj = get_user_share(user=i.bid_by,project=project)
				while i.lots_pending > 0:
					wallet_amount = Transactions.get_wallet_amount(i,user=i.bid_by)

					if wallet_amount > 0:
						possible_solutions_of_limit = []
						if i.order_type == 'limit':
							possible_solutions_of_limit = [j for j in limit_ask if j.limit_price <= i.limit_price]
						elif i.order_type == 'market':
							possible_solutions_of_limit = limit_ask

						if possible_solutions_of_limit:
							best_possible_solution = min([j.limit_price for j in possible_solutions_of_limit])
							
							if market_ask and best_possible_solution > project.market_price and project.market_price.amount != 0.0:
								for m in market_ask:
									user_company_shares_obj = UserCompanyShares.objects.filter(user=m.ask_by,project=project).first()
									shares = i.lots_pending if m.lots_pending > i.lots_pending else m.lots_pending
									wallet_amount = Transactions.get_wallet_amount(i,user=i.bid_by)
									shares_to_buy = round(wallet_amount / project.market_price.amount)
									if shares_to_buy > 0:
										actual_shares = shares if shares_to_buy >= shares else shares_to_buy

										total_price = actual_shares * project.market_price.amount
										OrderBook.objects.create(buyer=i.bid_by,seller=m.ask_by,
																project=project,bid_id=i,ask_id=m,
																shares=actual_shares,price=project.market_price
															)

										data = [{
												"remark": "Buy Share",
												"mode": "withdrawal",
												"status": "success",
												"amount":{"amount": total_price,"currency":"USD"},
												"user": i.bid_by.id
											},
											{
												"remark": "Sell Share",
												"mode": "deposite",
												"status": "success",
												"amount":{"amount": total_price,"currency":"USD"},
												"user": m.ask_by.id
											}
										]

										transaction = TransactionsSerializer(data=data,many=True)
										transaction.is_valid(raise_exception=True)
										transaction.save(project=project)

										m.lots_sold += actual_shares
										m.lots_pending = m.quantity-m.lots_sold
										if m.lots_pending==0:
											m.is_closed = True
											market_ask.remove(m)
										m.save()
										i.lots_filled += actual_shares
										i.lots_pending = i.quantity-i.lots_filled
										if i.lots_pending==0:
											i.is_closed = True
										i.save()
										if m.exchange_type == "isx" and user_company_shares_obj:
											user_company_shares_obj.isx_share_to_sell -= actual_shares
											bidder_share_obj.isx_shares += actual_shares
											bidder_share_obj.save()
											user_company_shares_obj.save()
										elif m.exchange_type == "lsx" and user_company_shares_obj:
											user_company_shares_obj.lsx_share_to_sell -= actual_shares
											bidder_share_obj.lsx_shares += actual_shares
											bidder_share_obj.save()
											user_company_shares_obj.save()
									else:
										break

									
							else:
								a = [j for j in possible_solutions_of_limit if j.limit_price == best_possible_solution]
								user_company_shares_obj = UserCompanyShares.objects.filter(user=a[0].ask_by,project=project).first()
								shares = i.lots_pending if a[0].lots_pending > i.lots_pending else a[0].lots_pending
								wallet_amount = Transactions.get_wallet_amount(i,user=i.bid_by)
								shares_to_buy = round(wallet_amount / a[0].limit_price.amount)
								if shares_to_buy > 0:
									actual_shares = shares if shares_to_buy >= shares else shares_to_buy
									
									total_price = actual_shares * a[0].limit_price.amount

									OrderBook.objects.create(buyer=i.bid_by,seller=a[0].ask_by,
															project=project,bid_id=i,ask_id=a[0],
															shares=actual_shares,price=a[0].limit_price
														)

									data = [{
											"remark": "Buy Share",
											"mode": "withdrawal",
											"status": "success",
											"amount":{"amount": total_price,"currency":"USD"},
											"user": i.bid_by.id
										},
										{
											"remark": "Sell Share",
											"mode": "deposite",
											"status": "success",
											"amount":{"amount": total_price,"currency":"USD"},
											"user": a[0].ask_by.id
										}
									]

									transaction = TransactionsSerializer(data=data,many=True)
									transaction.is_valid(raise_exception=True)
									transaction.save(project=project)

									a[0].lots_sold += actual_shares
									a[0].lots_pending = a[0].quantity-a[0].lots_sold
									if a[0].lots_pending==0:
										a[0].is_closed = True
										limit_ask.remove(a[0])
									a[0].save()
									i.lots_filled += actual_shares
									i.lots_pending = i.quantity-i.lots_filled
									if i.lots_pending==0:
										i.is_closed = True
									i.save()
									project.market_price = a[0].limit_price
									project.save()
									if a[0].exchange_type == "isx" and user_company_shares_obj:
										user_company_shares_obj.isx_share_to_sell -= actual_shares
										bidder_share_obj.isx_shares += actual_shares
										bidder_share_obj.save()
										user_company_shares_obj.save()
									elif a[0].exchange_type == "lsx" and user_company_shares_obj:
										user_company_shares_obj.lsx_share_to_sell -= actual_shares
										bidder_share_obj.lsx_shares += actual_shares
										bidder_share_obj.save()
										user_company_shares_obj.save()
								else:
									break
						elif not possible_solutions_of_limit and market_ask and ((i.order_type=="market" and project.market_price.amount != 0.0) or (i.order_type=="limit" and project.market_price <= i.limit_price)):
							for m in market_ask:
								user_company_shares_obj = UserCompanyShares.objects.filter(user=m.ask_by,project=project).first()
								shares = i.lots_pending if m.lots_pending > i.lots_pending else m.lots_pending
								wallet_amount = Transactions.get_wallet_amount(i,user=i.bid_by)
								shares_to_buy = round(wallet_amount / project.market_price.amount)
								if shares_to_buy > 0:
									actual_shares = shares if shares_to_buy >= shares else shares_to_buy
									total_price = actual_shares * project.market_price.amount

									OrderBook.objects.create(buyer=i.bid_by,seller=m.ask_by,
															project=project,bid_id=i,ask_id=m,
															shares=actual_shares,price=project.market_price
														)

									data = [{
											"remark": "Buy Share",
											"mode": "withdrawal",
											"status": "success",
											"amount":{"amount": total_price,"currency":"USD"},
											"user": i.bid_by.id
										},
										{
											"remark": "Sell Share",
											"mode": "deposite",
											"status": "success",
											"amount":{"amount": total_price,"currency":"USD"},
											"user": m.ask_by.id
										}
									]

									transaction = TransactionsSerializer(data=data,many=True)
									transaction.is_valid(raise_exception=True)
									transaction.save(project=project)

									m.lots_sold += actual_shares
									m.lots_pending = m.quantity-m.lots_sold
									if m.lots_pending==0:
										m.is_closed = True
										market_ask.remove(m)
									m.save()
									i.lots_filled += actual_shares
									i.lots_pending = i.quantity-i.lots_filled
									if i.lots_pending==0:
										i.is_closed = True
									i.save()
									if m.exchange_type == "isx" and user_company_shares_obj:
										user_company_shares_obj.isx_share_to_sell -= actual_shares
										bidder_share_obj.isx_shares += actual_shares
										bidder_share_obj.save()
										user_company_shares_obj.save()
									elif m.exchange_type == "lsx" and user_company_shares_obj:
										user_company_shares_obj.lsx_share_to_sell -= actual_shares
										bidder_share_obj.lsx_shares += actual_shares
										bidder_share_obj.save()
										user_company_shares_obj.save()
								else:
									break
						else:
							break
					else:
						break
		                                
	return HttpResponse(json.dumps({"message":"success"}), content_type="application/json")
