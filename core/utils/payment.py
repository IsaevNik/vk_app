import hashlib


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
