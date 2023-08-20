import orjson
from aiokafka import AIOKafkaProducer


async def send_event(topic: str, data: dict):
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    # Get cluster layout and initial topic/partition leadership information
    await producer.start()
    try:
        # Produce message
        await producer.send_and_wait(topic, orjson.dumps(data))
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()
