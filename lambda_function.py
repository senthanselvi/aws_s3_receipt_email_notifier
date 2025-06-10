import json
import os
import boto3
import uuid
from datetime import datetime
import urllib.parse
 
s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
 
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'Receipts')
SES_SENDER_EMAIL = os.environ.get('SES_SENDER_EMAIL', 'senthanselvi.m@gmail.com')
SES_RECIPIENT_EMAIL = os.environ.get('SES_RECIPIENT_EMAIL', 'senthanselvi.m@gmai.com')

def lambda_handler(event, context):
    try:
        # Get the S3 bucket and key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        # URL decode the key to handle spaces and special characters
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

        print(f"Processing receipt from {bucket}/{key}")
 
        try:
            s3.head_object(Bucket=bucket, Key=key)
            print(f"Object verification successful: {bucket}/{key}")
        except Exception as e:
            print(f"Object verification failed: {str(e)}")
            raise Exception(f"Unable to access object {key} in bucket {bucket}: {str(e)}")
 
        receipt_data = process_receipt_with_textract(bucket, key)
 
        store_receipt_in_dynamodb(receipt_data, bucket, key)
 
        send_email_notification(receipt_data)

        return {
            'statusCode': 200,
            'body': json.dumps('Receipt processed successfully!')
        }
    except Exception as e:
        print(f"Error processing receipt: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def process_receipt_with_textract(bucket, key):
    """Process receipt using Textract's AnalyzeExpense operation"""
    try:
        print(f"Calling Textract analyze_expense for {bucket}/{key}")
        response = textract.analyze_expense(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        print("Textract analyze_expense call successful")
    except Exception as e:
        print(f"Textract analyze_expense call failed: {str(e)}")
        raise
 
    receipt_id = str(uuid.uuid4())
 
    receipt_data = {
        'receipt_id': receipt_id,
        'date': datetime.now().strftime('%Y-%m-%d'),   
        'vendor': 'Unknown',
        'total': '0.00',
        'items': [],
        's3_path': f"s3://{bucket}/{key}"
    }
 
    if 'ExpenseDocuments' in response and response['ExpenseDocuments']:
        expense_doc = response['ExpenseDocuments'][0]
 
        if 'SummaryFields' in expense_doc:
            for field in expense_doc['SummaryFields']:
                field_type = field.get('Type', {}).get('Text', '')
                value = field.get('ValueDetection', {}).get('Text', '')

                if field_type == 'TOTAL':
                    receipt_data['total'] = value
                elif field_type == 'INVOICE_RECEIPT_DATE':
                    try:
                        receipt_data['date'] = value
                    except:
                        pass
                elif field_type == 'VENDOR_NAME':
                    receipt_data['vendor'] = value
 
        if 'LineItemGroups' in expense_doc:
            for group in expense_doc['LineItemGroups']:
                if 'LineItems' in group:
                    for line_item in group['LineItems']:
                        item = {}
                        for field in line_item.get('LineItemExpenseFields', []):
                            field_type = field.get('Type', {}).get('Text', '')
                            value = field.get('ValueDetection', {}).get('Text', '')

                            if field_type == 'ITEM':
                                item['name'] = value
                            elif field_type == 'PRICE':
                                item['price'] = value
                            elif field_type == 'QUANTITY':
                                item['quantity'] = value
 
                        if 'name' in item:
                            receipt_data['items'].append(item)

    print(f"Extracted receipt data: {json.dumps(receipt_data)}")
    return receipt_data

def store_receipt_in_dynamodb(receipt_data, bucket, key):
    """Store the extracted receipt data in DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
 
        items_for_db = []
        for item in receipt_data['items']:
            items_for_db.append({
                'name': item.get('name', 'Unknown Item'),
                'price': item.get('price', '0.00'),
                'quantity': item.get('quantity', '1')
            })
 
        db_item = {
            'receipt_id': receipt_data['receipt_id'],
            'date': receipt_data['date'],
            'vendor': receipt_data['vendor'],
            'total': receipt_data['total'],
            'items': items_for_db,
            's3_path': receipt_data['s3_path'],
            'processed_timestamp': datetime.now().isoformat()
        }
 
        table.put_item(Item=db_item)
        print(f"Receipt data stored in DynamoDB: {receipt_data['receipt_id']}")
    except Exception as e:
        print(f"Error storing data in DynamoDB: {str(e)}")
        raise

def send_email_notification(receipt_data):
    """Send an email notification with receipt details"""
    try:
        items_html = ""
        for item in receipt_data['items']:
            name = item.get('name', 'Unknown Item')
            price = item.get('price', 'N/A')
            quantity = item.get('quantity', '1')
            items_html += f"<li>{name} - ${price} x {quantity}</li>"

        if not items_html:
            items_html = "<li>No items detected</li>"
 
        html_body = f"""
        <html>
        <body>
            <h2>Receipt Processing Notification</h2>
            <p><strong>Receipt ID:</strong> {receipt_data['receipt_id']}</p>
            <p><strong>Vendor:</strong> {receipt_data['vendor']}</p>
            <p><strong>Date:</strong> {receipt_data['date']}</p>
            <p><strong>Total Amount:</strong> ${receipt_data['total']}</p>
            <p><strong>S3 Location:</strong> {receipt_data['s3_path']}</p>

            <h3>Items:</h3>
            <ul>
                {items_html}
            </ul>

            <p>The receipt has been processed and stored in DynamoDB.</p>
        </body>
        </html>
        """
 
        ses.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={
                'ToAddresses': [SES_RECIPIENT_EMAIL]
            },
            Message={
                'Subject': {
                    'Data': f"Receipt Processed: {receipt_data['vendor']} - ${receipt_data['total']}"
                },
                'Body': {
                    'Html': {
                        'Data': html_body
                    }
                }
            }
        )

        print(f"Email notification sent to {SES_RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"Error sending email notification: {str(e)}")
        print("Continuing execution despite email error")