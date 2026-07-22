from config.logging_config import setup_logger

logger = setup_logger()

logger.info("Application started.")

logger.warning("This is a warning.")

logger.error("This is an error.")