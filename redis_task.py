import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")



async def get_redis_connection():
    return redis.ConnectionPool.from_url(
        REDIS_URL,
        max_connections=10, 
        decode_responses=True
    )



async def add_task(connection, task_data):
    try:
        task_id = task_data['id']
        if await connection.get(task_id):
            print(f"Task with ID {task_id} already exists.")
            return True
        else:
            value = json.dumps(task_data) 
            await connection.setex(task_id, 3600, value)
            return True
    except Exception as e:
        print(f"Failed to add task: {e}")
        return False
    
async def get_task(connection, task_id):
    try:
        data = await connection.get(task_id)
        if data:
            await connection.delete(task_id)
            return json.loads(data)
        else:
            return None
    except Exception as e:
        print(f"Failed to get task: {e}")
        return None
