import pika
import json
from src.config import settings
from typing import Callable, Optional
from src.models import Transaction, Block


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
    
    def initialize(self):
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.channel.queue_declare(queue='transactions', durable=True)
            self.channel.queue_declare(queue='blocks', durable=True)
            self.channel.queue_declare(queue='mining', durable=True)
            
            print("Conexión a RabbitMQ establecida correctamente")
        except Exception as e:
            print(f"Error conectando a RabbitMQ: {e}")
            raise
    
    def publish_transaction(self, transaction: Transaction) -> bool:
        try:
            message = json.dumps(transaction.to_dict())
            self.channel.basic_publish(
                exchange='',
                routing_key='transactions',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            return True
        except Exception as e:
            print(f"Error publicando transacción: {e}")
            return False
    
    def consume_transactions(self, callback: Callable) -> None:
        try:
            def on_message(ch, method, properties, body):
                try:
                    tx_data = json.loads(body)
                    transaction = Transaction(**tx_data)
                    callback(transaction)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Error procesando mensaje: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
            self.channel.basic_consume(
                queue='transactions',
                on_message_callback=on_message
            )
            self.channel.start_consuming()
        except Exception as e:
            print(f"Error consumiendo transacciones: {e}")

    def consume_blocks(self, callback: Callable) -> None:
        """
        Consume mensajes de la cola de bloques y ejecuta el callback por cada bloque.
        Se espera que el callback reciba un dict con los datos del bloque.
        """
        try:
            def on_message(ch, method, properties, body):
                try:
                    block_data = json.loads(body)
                    callback(block_data)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Error procesando bloque desde RabbitMQ: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            self.channel.basic_consume(
                queue='blocks',
                on_message_callback=on_message
            )
            self.channel.start_consuming()
        except Exception as e:
            print(f"Error consumiendo bloques: {e}")
    
    def publish_block(self, block: Block) -> bool:
        try:
            block_data = {
                'index': block.index,
                'timestamp': block.timestamp.isoformat(),
                'transactions': [tx.to_dict() for tx in block.transactions],
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            }
            message = json.dumps(block_data)
            self.channel.basic_publish(
                exchange='',
                routing_key='blocks',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            return True
        except Exception as e:
            print(f"Error publicando bloque: {e}")
            return False
    
    def publish_mining_request(self, mining_address: str) -> bool:
        try:
            message = json.dumps({'mining_address': mining_address})
            self.channel.basic_publish(
                exchange='',
                routing_key='mining',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            return True
        except Exception as e:
            print(f"Error publicando solicitud de minería: {e}")
            return False
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()


rabbitmq_client = RabbitMQClient()

