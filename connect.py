import mysql.connector

# Helper function to get a database connection
def get_database_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="repository"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None