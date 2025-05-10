import boto3
import re
import requests
import math
import urllib.parse
import socket
from requests_aws4auth import AWS4Auth

region = 'us-east-1'  # <-- Make sure this matches your OpenSearch region!
service = 'es'
# credentials = boto3.Session().get_credentials()
# awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'https://vpc-my-search-domain-yaffw5qx3bcejmc4xebwzncxjm.us-east-1.es.amazonaws.com'
index = 'mygoogle'
datatype = '_doc'
headers = { "Content-Type": "application/json" }
s3 = boto3.client('s3')

def listToString(s):
    str1 = ""
    for ele in s:
        if isinstance(ele, bytes):
            str1 += ele.decode()
        else:
            str1 += str(ele)
    return str1

def handler(event, context):
    print("Lambda handler started")
    credentials = boto3.Session().get_credentials()
    print("Credentials:", credentials)
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    print("Credentials access key:", credentials.access_key)
    print("Credentials secret key:", credentials.secret_key)
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        print("About to fetch from S3")
        print("Bucket:", bucket)
        print("Key:", key)
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
            print("Fetched from S3")
        except Exception as e:
            print("Error fetching from S3:", e)
            raise
        print("Fetched from S3")
        body = obj['Body'].read()
        lines = body.splitlines()
        cust_id = urllib.parse.quote_plus(key)
        url = f"{host}/{index}/{datatype}/{cust_id}"
        title = lines[0]
        author = lines[1]
        date = lines[2]
        final_body = lines[3:]
        summary = final_body[1:2]
        document = {
            "Title": title,
            "Author": author,
            "Date": date,
            "Body": listToString(final_body),
            "Summary": summary
        }
        print("About to resolve OpenSearch endpoint")
        print(socket.gethostbyname('vpc-my-search-domain-yaffw5qx3bcejmc4xebwzncxjm.us-east-1.es.amazonaws.com'))
        print("About to send request to OpenSearch")
        try:
            r = requests.post(url, auth=awsauth, json=document, headers=headers)
            print("OpenSearch response:", r.text)
        except Exception as e:
            print("Error posting to OpenSearch:", e)
    return {
        "statusCode": 200,
        "body": "Done"
    }