import hashlib
import json

import logging
import requests


logger = logging.getLogger('payment')


class BadResponse(Exception):
    pass


class PaymentFacade:

    terminal_url = 'https://www.free-kassa.ru/merchant/cash.php'
    merchand = '51227'
    secret1 = 'gowxko6r'
    secret2 = 'lbsrwwmi'

    def get_terminal(self, amount, order_id):
        seq = list(map(str, [self.merchand, amount, self.secret1, order_id]))
        sign = self._get_sign(seq)
        params = dict(m=self.merchand, oa=amount, o=order_id, s=sign)
        return '/?'.join([self.terminal_url,
                         '&'.join(['{}={}'.format(k, v) for k, v in params.items()])])

    def check_sign(self, params):
        order_id = params.get('MERCHANT_ORDER_ID')
        amount = params.get('AMOUNT')
        sign = params.get('SIGN')
        seq = list(map(str, [self.merchand, amount, self.secret2, order_id]))
        system_sign = self._get_sign(seq)
        return (False, True)[system_sign == sign]

    @staticmethod
    def _get_sign(seq):
        line = ':'.join(key for key in seq)
        return hashlib.md5(line.encode('utf-8')).hexdigest()


payment_facade = PaymentFacade()


class CashSender:

    merchand = '51227'
    api_key = 'api_key'

    url = 'https://wallet.free-kassa.ru/api_v1.php'
    BALANCE, CASHOUT, STATUS = 'balance', 'cashout', 'status'
    ACTIONS = {
        BALANCE: 'get_balance',
        CASHOUT: 'cashout',
        STATUS: 'get_payment_status'
    }

    def request(self, data):
        response = requests.post(url=self.url, data=data)
        try:
            response = json.loads(response.content.decode('utf-8'))
            if response and response.get('data'):
                return response
            else:
                logger.error(response)
                raise BadResponse
        except ValueError:
            return None

    def get_balance(self):
        params = {
            'wallet_id': self.merchand,
            'sign': self._get_sign([self.merchand, self.api_key]),
            'action': self.ACTIONS[self.BALANCE]
        }
        try:
            response = self.request(params)
            return response.get('data').get('RUR')
        except BadResponse:
            return None

    def cash_send(self, wallet, amount):
        params = {
            'wallet_id': self.merchand,
            'purse': wallet.purse,
            'amount': amount,
            'currency': wallet.currency,
            'desc': 'cash send',
            'sign': self._get_sign([self.merchand, wallet.currency,
                                    amount, wallet.purse, self.api_key]),
            'action': self.ACTIONS[self.CASHOUT],
        }
        try:
            response = self.request(params)
            return response.get('data').get('payment_id')
        except BadResponse:
            return None

    def get_status(self, payment_id):
        params = {
            'wallet_id': self.merchand,
            'payment_id': payment_id,
            'sign': self._get_sign([self.merchand, payment_id, self.api_key]),
            'action': self.ACTIONS[self.STATUS],
        }
        try:
            response = self.request(params)
            return response.get('data').get('status')
        except BadResponse:
            return None

    @staticmethod
    def _get_sign(seq):
        line = ':'.join(str(key) for key in seq)
        return hashlib.md5(line.encode('utf-8')).hexdigest()


cash_sender = CashSender()
