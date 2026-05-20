import redis
import logging

logger = logging.getLogger(__name__)
try:
    redis_client = redis.Redis(host="redis_cache",port=6379,decode_responses=True)
    redis_client.ping()
    logger.info("Successfully connected to Redis Cache instance!")


except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None