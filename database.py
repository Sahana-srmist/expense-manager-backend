import psycopg2

def get_db_connection():
    return psycopg2.connect(
        dbname="expense manager final",
        user="postgres",
        password="Sahana@2006",  # In real app, use env variables
        host="localhost",
        port="5432"
    )
