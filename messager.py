import boto3
import json
import time
import random
import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

#slack_token = os.environ['SLACK_TOKEN']  
#channel_id = os.environ['CHANNEL_ID']
#dynamodb_table = os.environ['DYNAMODB_TABLE']


def lambda_handler(event, context):
    try:    
        slack_event = json.loads(event['body'])
        user, message = parse_slack_message(slack_event)
        cleaned_data = clean_message_data(message)
        
        log_id = generate_log_id()
        cleaned_data['logid'] = log_id
        cleaned_data['username'] = user

        insert_into_dynamodb(cleaned_data)

        #send_confirmation_to_slack(log_id)
        logger.info(f"Message processed and logged with LogID: {log_id}")
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        raise
    
    
def parse_slack_message(slack_event):
    user = slack_event['username']
    message = slack_event['text']
    return user, message


def clean_message_data(message):
    data = {}
    if '--->' in message:
        lines = message.split('\n')
        for line in lines:
            if '--->' in line:
                key, value = line.split('--->', 1)
                key = key.strip().replace(' ', '')
                data[key] = value.strip()
    else:
        data['message'] = message.strip()
    return data


def generate_log_id():
    timestamp = int(time.time())
    random_number = random.randint(1000, 9999)
    return f"{timestamp}{random_number}"


def insert_into_dynamodb(data):
    try:    
        dynamodb = boto3.client('dynamodb')
        dynamodb.put_item(
            TableName=dynamodb_table,
            Item={k: {'S': str(v)} for k, v in data.items()}
        )
        logger.info("Data inserted into DynamoDB successfully.")
    except Exception as e:
        logger.error(f"Error inserting data into DynamoDB: {str(e)}")
        raise


'''
def send_confirmation_to_slack(log_id):
    client = WebClient(token=slack_token)
    confirmation_message = f"Error logged successfully under LogID {log_id}"

    try:
        client = WebClient(token=slack_token)
        confirmation_message = f"Log logged successfully under LogID {log_id}"
        response = client.chat_postMessage(channel=channel_id, text=confirmation_message)
        logger.info("Confirmation sent to Slack successfully.")
    except SlackApiError as e:
        logger.error(f"Error sending message to Slack: {e.response['error']}")
        raise
'''