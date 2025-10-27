import datetime
import json
from data_structures.tutorial.models import *

def has_foreign_currencies(customer: Customer) -> bool:
    '''Функция определяет, есть ли у клиента кредит в иностранной валюте'''
    for item in customer.loans:
        if item.currency != "RUR" :
            print("Обнаружены кредиты в иностранной валюте")
            return True
    print("Кредиты в иностранной валюте не обнаружены")
    return False


def parse_currency_rates(currency_rate_response, currency_name: str) -> float:
    '''Функция возвращает курс платёжной валюты в рублях'''
    body_string = currency_rate_response['body']
    body_json = json.loads(body_string)

    return body_json['Valute'][currency_name]['Value']