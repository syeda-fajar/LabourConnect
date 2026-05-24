
import os
import redis
import logging

logger = logging.getLogger(__name__)


REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    try:
        logger.info("REDIS_URL found. Attempting to connect to Redis...")
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        logger.info(" Successfully connected to Redis Cache instance!")
    except Exception as e:
        logger.error(f" Failed to connect to Redis via URL: {e}. Falling back to Database.")
        redis_client = None
else:
   
    logger.warning("ℹ REDIS_URL environment variable not found. Caching will be disabled.")
    redis_client = None