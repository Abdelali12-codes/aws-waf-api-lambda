import sys
import logging
import os
import pymysql
import boto3
import json
import requests

# rds settings
rds_host = os.environ['RDS_HOST']
name = os.environ['RDS_USERNAME']
secret_name = os.environ['SECRET_NAME']
db_name = os.environ['RDS_DB_NAME']
table_name = os.environ['RDS_Table_NAME']

my_session = boto3.session.Session()
region_name = my_session.region_name
conn = None

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def openConnection():
    global conn
    password = "None"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',region_name=region_name)

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        print(get_secret_value_response)
    except ClientError as e:
        print(e)
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            j = json.loads(secret)
            password = j['password']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            print("password binary:" + decoded_binary_secret)
            password = decoded_binary_secret.password

    try:
        #print("Opening Connection")
        if(conn is None):
            conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
        elif (not conn.open):
            # print(conn.open)
            conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    except Exception as e:
        print (e)
        print("ERROR: Unexpected error: Could not connect to MySql instance.")
        raise e

# CloudFormation uses a pre-signed S3 URL to receive the response back from the custom resources managed by it. This is a simple function
# which shall be used to send the response back to CFN custom resource by performing PUT request to the pre-signed S3 URL.
def sendResponse(event, context, responseStatus, responseData, physicalResourceId):
    responseUrl = event['ResponseURL']

    # print responseUrl
    print(event)
    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + \
        context.log_stream_name
    responseBody['PhysicalResourceId'] = context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    responseBody['Data'] = responseData

    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))

def lambda_handler(event, context):
    responseData = {}
    responseStatus = 'SUCCESS'
    if event['RequestType'] == 'Delete':
        sendResponse(event, context, responseStatus, responseData, None)
        return True

    try:
        # Create Table and insert sample data
        openConnection()
        item_count = 0

        with conn.cursor() as cur:
            #Create DB
            #cur.execute("create database playersdb")
            cur.execute('use '+ db_name)
            #Create Table
            create_table_sql = 'create table ' + table_name +  '( id  int NOT NULL, Name varchar(255) NOT NULL, PRIMARY KEY (id))'
            #cur.execute("create table Players ( id  int NOT NULL, Name varchar(255) NOT NULL, PRIMARY KEY (id))")
            cur.execute(create_table_sql)
            cur.execute('insert into ' + table_name + ' (id, Name) values(1, "Lionel Messi")')
            cur.execute('insert into ' + table_name + ' (id, Name) values(2, "Cristiano Ronaldo")')
            cur.execute('insert into ' + table_name + ' (id, Name) values(3, "Son Heung-min")')
            conn.commit()
            cur.execute('select * from ' + table_name)
            #Check number of rows we inserted in new RDS
            for row in cur:
                item_count += 1
                logger.info(row)
                print(row)
            print("Added %d items from RDS MySQL table" %(item_count))

    except Exception as e:
        # Error while opening connection or processing
        print(e)
        responseStatus = 'FAILED'
    finally:
        #print("Closing Connection")
        if(conn is not None and conn.open):
            conn.close()
        # send response back to CFN
        sendResponse(event, context, responseStatus, responseData, None)
    return True
