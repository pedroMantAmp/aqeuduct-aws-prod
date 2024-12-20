"""
AWS Lambda Function to Synchronize Client Data from Supabase to AWS RDS.

This script handles incoming webhook payloads, parses the data,
and synchronizes it with the `clients` table in an AWS RDS PostgreSQL database.
The script includes the following functionalities:
1. Parsing payload data to map it to database columns.
2. Executing parameterized SQL queries to insert or update data in RDS.
3. Comprehensive error handling for missing payload keys and database errors.

Modules:
    - json: For handling JSON payloads.
    - psycopg2: For connecting to and executing queries in PostgreSQL.

Environment:
    - Requires access to AWS RDS PostgreSQL database credentials and network.

Constants:
    - RDS_CONFIG: Contains database connection details.
    - SQL_INSERT_UPDATE_CLIENT: Parameterized SQL query for inserting or updating data.

Functions:
    - parse_payload(event): Parses the incoming webhook event payload.
    - execute_query(query, data): Executes SQL queries on the RDS database.
    - lambda_handler(event, _): Main Lambda handler function.

Author:
    [Your Name/Team Name]

Date:
    [Insert Date Here]

"""

import json
import psycopg2

# RDS Configuration
RDS_CONFIG = {
    "host": "aqueduct.c78eqesmgw14.us-east-2.rds.amazonaws.com",  # POSTGRES_HOST
    "dbname": "postgres",                                         # POSTGRES_DB
    "user": "aqueduct_admin",                                     # POSTGRES_USER
    "password": "StrongPassword123!"                              # POSTGRES_PASSWORD
}

# SQL Query to insert or update a client in RDS
SQL_INSERT_UPDATE_CLIENT = """
    INSERT INTO public.clients (
        clientid, clientname, aqueductclientnumber, dba, 
        streetaddress, city, state, zip, country, createdat
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (clientid) DO UPDATE SET
        clientname = EXCLUDED.clientname,
        aqueductclientnumber = EXCLUDED.aqueductclientnumber,
        dba = EXCLUDED.dba,
        streetaddress = EXCLUDED.streetaddress,
        city = EXCLUDED.city,
        state = EXCLUDED.state,
        zip = EXCLUDED.zip,
        country = EXCLUDED.country,
        createdat = EXCLUDED.createdat;
"""

def parse_payload(event):
    """
    Parse the incoming payload from the event.

    Args:
        event (dict): The incoming webhook event.

    Returns:
        tuple: The mapped client data ready for the SQL query.

    Raises:
        KeyError: If a required key is missing in the payload.
    """
    payload = json.loads(event['body'])
    return (
        payload['clientid'],                  # clientid
        payload['clientname'],                # clientname
        payload['aqueductclientnumber'],      # aqueductclientnumber
        payload.get('dba', None),             # dba (optional)
        payload['streetaddress'],             # streetaddress
        payload['city'],                      # city
        payload['state'],                     # state
        payload['zip'],                       # zip
        payload['country'],                   # country
        payload['createdat']                  # createdat
    )

def execute_query(query, data):
    """
    Execute the given query with the provided data.

    Args:
        query (str): The SQL query to execute.
        data (tuple): The data to use in the query.

    Returns:
        None

    Raises:
        Exception: If a database error occurs.
    """
    conn = None  # Initialize conn to avoid reference errors
    try:
        # Connect to Amazon RDS
        conn = psycopg2.connect(**RDS_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()
    except psycopg2.Error as db_error:
        raise Exception(f"Database error: {str(db_error)}")
    finally:
        if conn:
            conn.close()

def lambda_handler(event, _):
    """
    AWS Lambda function to synchronize client data from Supabase to AWS RDS.

    Args:
        event (dict): The incoming webhook event containing client data.
        _ (object): Lambda context (unused).

    Returns:
        dict: Response object with status code and message.

    Raises:
        Exception: For unhandled errors.
    """
    try:
        # Parse the payload
        client_data = parse_payload(event)

        # Execute the SQL query
        execute_query(SQL_INSERT_UPDATE_CLIENT, client_data)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Client synchronized successfully"})
        }

    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing key in payload: {str(e)}"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }