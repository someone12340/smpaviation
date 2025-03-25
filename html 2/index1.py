import mysql.connector
from mysql.connector import Error

hostname = "te3xi.h.filess.io"
database = "FLIGHTS_usingrate"
port = "61002"
username = "FLIGHTS_usingrate"
password = "6d8c67d4b9c0ea31f7312b543c6b73c418398d7d"

try:
    connection = mysql.connector.connect(host=hostname, database=database, user=username, password=password, port=port)
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)

except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

