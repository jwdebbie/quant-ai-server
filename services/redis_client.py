"""
Redis 연결 설정. B가 price:{stock_code} 형식으로 현재가를 write하는 그 Redis와
같은 인스턴스를 가리켜야 합니다. REDIS_HOST/PORT는 실제 배포 환경의 .env 값으로 교체하세요.
"""

import os

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

_redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_redis_client():
    return _redis_client
