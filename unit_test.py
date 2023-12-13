import unittest
from unittest.mock import patch, MagicMock
from moto import mock_dynamodb2
import boto3
from messager import (parse_slack_message, clean_message_data, 
                              generate_log_id, insert_into_dynamodb, 
                              send_confirmation_to_slack)


class TestLambdaFunctions(unittest.TestCase):

    def setUp(self):
        self.mock_dynamodb = mock_dynamodb2()
        self.mock_dynamodb.start()
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = 'mock_table'
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[{'AttributeName': 'LogID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'LogID', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )

    def tearDown(self):
        self.mock_dynamodb.stop()

    def test_parse_slack_message(self):
        slack_event = {
            'username': 'incoming-webhook',
            'text': 'Test message'
        }
        user, message = parse_slack_message(slack_event)
        self.assertEqual(user, 'incoming-webhook')
        self.assertEqual(message, 'Test message')

    def test_clean_message_data(self):
        message = (":tada: :clap:  prod-uwf-ecs-auto-scale-2000 state is now OK.\n"
                   "AlarmName--->prod-uwf-ecs-auto-scale-2000\n"
                   "AlarmDescription--->UWF ECS auto scale alarm\n"
                   "AWSAccountId--->617721543900\n")
        expected_data = {
            'AlarmName': 'prod-uwf-ecs-auto-scale-2000',
            'AlarmDescription': 'UWF ECS auto scale alarm',
            'AWSAccountId': '617721543900'
        }
        data = clean_message_data(message)
        self.assertEqual(data, expected_data)

    def test_generate_log_id(self):
        log_id = generate_log_id()
        self.assertIsInstance(log_id, str)
        self.assertRegex(log_id, r'^\d{10}\d{4}$')  # Assuming your ID format

    def test_insert_into_dynamodb(self):
        data = {'LogID': '123', 'username': 'incoming-webhook', 'message': 'Test message'}
        insert_into_dynamodb(data, self.table_name)
        response = self.table.get_item(Key={'LogID': '123'})
        self.assertEqual(response['Item'], data)

    @patch('messager.WebClient')
    def test_send_confirmation_to_slack(self, mock_slack):
        mock_slack.return_value.chat_postMessage = MagicMock(return_value=True)
        log_id = '123'
        send_confirmation_to_slack(log_id)
        mock_slack.return_value.chat_postMessage.assert_called_with(channel='YOUR_CHANNEL_ID', text=f"Log logged successfully under LogID {log_id}")

if __name__ == '__main__':
    unittest.main()
