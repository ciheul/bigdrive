import pika


class PikaConnection(object):
    QUEUE = 'test'
    EXCHANGE = ''
    HOST = 'localhost'

    def __init__(self):
        self.connection = None
        self.channel = None

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.HOST))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.QUEUE)

    def publish_message(self, message):
        if self.connection is None:
            # NOTE use raise
            return

        print message
        self.channel.basic_publish(exchange=self.EXCHANGE,
                                   routing_key=self.QUEUE,
                                   body=message)

    def close(self):
        self.connection.close()

    def instance(self):
        return self.connection
