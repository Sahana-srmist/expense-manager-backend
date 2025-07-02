import psycopg2
import os
from urllib.parse import urlparse

import os
import psycopg2

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL not set in environment variables.")
    return psycopg2.connect(db_url)

