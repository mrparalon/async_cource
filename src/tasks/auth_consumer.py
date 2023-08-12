from aiokafka import AIOKafkaConsumer
from loguru import logger


async def tasks_auth_worker():
    consumer = AIOKafkaConsumer(
        "auth",
        bootstrap_servers="localhost:9092",
        group_id="tasks_auth",
        enable_auto_commit=True,  # Is True by default anyway
        auto_commit_interval_ms=1000,  # Autocommit every second
        auto_offset_reset="earliest",  # If committed offset not found, start
    )
    # Get cluster layout and join group `my-group`
    await consumer.start()
    logger.info("consumer started")
    try:
        # Consume messages
        async for msg in consumer:
            logger.info(
                f"consumed: {msg.topic=}, {msg.partition=}, {msg.offset=} {msg.key=}, {msg.value=}, {msg.timestamp=}",
            )
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()
