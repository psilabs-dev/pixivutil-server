import os


class RabbitConfig:

    def __init__(self):
        self.broker_url = os.getenv("RABBITMQ_BROKER_URL", "amqp://guest:guest@rabbitmq:5672")

config = RabbitConfig()
