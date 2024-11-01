from connect import get_database_connection
import mysql.connector
import bcrypt
from config import Config


# Function to register a new user
def register_user(first_name=None, last_name=None, course=None, major=None, year_level=None, username=None, password=None, email=None):
    conn = get_database_connection()
    cursor = conn.cursor()

    # Query 1: Check if the user exists based on first name, last name, username, email, course, and major
    cursor.execute("""
        SELECT COUNT(*) FROM users 
        WHERE first_name = %s AND last_name = %s
        AND email = %s AND course = %s AND major = %s  AND username = %s;
    """, (first_name, last_name, email, course, major, username))
    user_exists = cursor.fetchone()[0]

    if user_exists:
        raise Exception("A user with the same details already exists.")

    # Query 2: Check if the username already exists
    cursor.execute("""
        SELECT COUNT(*) FROM users WHERE username = %s;
    """, (username,))
    username_exists = cursor.fetchone()[0]

    if username_exists:
        raise Exception("Username already exists.")

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert user data into the database
    try:
        cursor.execute("""
            INSERT INTO users (first_name, last_name, course, major, year_level, username, password_hash, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, course, major, year_level, username, password_hash, email))
        conn.commit()
        print("User registered successfully!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# Function to register a new admin
def register_admin(username=None, email=None, password=None):
    conn = get_database_connection()
    cursor = conn.cursor()

    # Check if the username or email already exists
    cursor.execute("SELECT COUNT(*) FROM admins WHERE username = %s OR email = %s", (username, email))
    admin_exists = cursor.fetchone()[0]

    if admin_exists:
        return False  # Username or email already exists

    # Hash the password
    password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Insert admin data into the database
    try:
        cursor.execute("""
        INSERT INTO admins (username, email, password)
        VALUES (%s, %s, %s)
        """, (username, email, password))
        conn.commit()
        print("Admin registered successfully!")
        return True  # Successful registration
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        return False  # Failed registration due to DB error
    finally:
        cursor.close()
        conn.close()


# Function to check the number of admins
def admin_count():
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admins")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return count

# Function to authenticate a user
def authenticate_user(username, password):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    user_data = cursor.fetchone()
    
    if user_data:
        stored_password_hash = user_data[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            cursor.close()
            conn.close()
            return True

# Function to authenticate admin
def authenticate_admin(username, password):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM admins WHERE username = %s", (username,))
    admin_data = cursor.fetchone()
    
    if admin_data:
        stored_password = admin_data[0]
        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            cursor.close()
            conn.close()
            return True


def change_user_password(username, new_password):
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        # Hash the new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Update the password in the database
        cursor.execute("UPDATE users SET password_hash = %s WHERE username = %s", (new_password_hash, username))
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_user_profile(user_id, first_name, last_name, username, email, course, major, year_level, profile_picture_url):
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users
            SET first_name = %s, last_name = %s, username = %s, email = %s, course = %s, major = %s, year_level = %s, profile_picture_url = %s
            WHERE user_id = %s
        """, (first_name, last_name, username, email, course, major, year_level, profile_picture_url, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def allowed_file(filename):
    return Config.allowed_file(filename)
