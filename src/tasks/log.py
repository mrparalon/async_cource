from loguru import logger


def log(message: str):
    logger.info(f"✅ {message}")
