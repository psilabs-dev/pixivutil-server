import os


class RabbitConfig:

    def __init__(self):
        self.broker_url = os.getenv("RABBITMQ_BROKER_URL", "amqp://guest:guest@rabbitmq:5672")
        self.management_url = os.getenv("RABBITMQ_MANAGEMENT_URL", "http://guest:guest@rabbitmq:15672")

config = RabbitConfig()
