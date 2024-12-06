from mytasks import invoke_payment

class MarketConnectorCelery:
    def sendPaymentTask(auction_uuid, expired_at):
        task = invoke_payment.apply_async((auction_uuid,), eta=expired_at)