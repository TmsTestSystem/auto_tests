import datetime
import json
from data_structures.tutorial.models import Customer

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
    if currency_name == 'RUR':
        return 1.0
    if isinstance(currency_rate_response, dict):
        body_string = currency_rate_response.get('body') or currency_rate_response.get('response')
    else:
        body_string = currency_rate_response
    if isinstance(body_string, bytes):
        body_string = body_string.decode('utf-8')
    if isinstance(body_string, dict):
        body_json = body_string
    else:
        body_json = json.loads(body_string)

    return body_json['Valute'][currency_name]['Value']
