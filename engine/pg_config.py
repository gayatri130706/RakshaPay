import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')
USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith('postgresql'))

def get_pg_params():
    if not USE_POSTGRES:
        return None
    import re
    m = re.match(r'postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)', DATABASE_URL)
    if not m:
        return None
    return {
        'user': m.group(1),
        'password': m.group(2),
        'host': m.group(3),
        'port': int(m.group(4)),
        'dbname': m.group(5),
    }
