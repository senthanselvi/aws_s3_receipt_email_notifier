# aws_s3_receipt_email_notifier
Serverless app that sends email notifications on new S3 receipt uploads using AWS Lambda and SES/SMTP.

Automated Receipt Email Notification via AWS S3 + Lambda

This project automates email notifications when a new file is uploaded to a specific prefix (`incoming/`) in an AWS S3 bucket.

**Project Overview**
- Monitors an S3 bucket for `s3:ObjectCreated:*` events
- Triggers an AWS Lambda function
- Sends an email notification (via SMTP or Amazon SES)

**Technologies Used**
- AWS S3
- Amazon SES / SMTP (Gmail)
- AWS IAM
- AWS DynamoDB
- AWS Lambda
- Python
- CloudWatch (for logs)
 
**Working**
1. A file is uploaded to the S3 bucket under `incoming/` path.
2. This triggers the Lambda function via S3 event notification.
3. The Lambda reads metadata and sends an email using SES or SMTP.

**Deployment Steps**
1. Create an S3 bucket and enable event trigger on `incoming/` prefix.
2. Deploy your Lambda function and assign an IAM role with:
   - S3 read permissions
   - SES or SMTP permissions
3. Configure email (verify in SES or enable Gmail SMTP).
4. Upload a test file to `incoming/` and check your email!

![image](https://github.com/user-attachments/assets/fbdc34c8-0fc9-4ba4-90f6-4e26e2c5294b)

![image](https://github.com/user-attachments/assets/c57a6dbc-86c4-4187-a6ee-31d4a8e361e8)

![image](https://github.com/user-attachments/assets/f6e2a9f9-6a47-4a53-8013-e978404abc89)

![image](https://github.com/user-attachments/assets/f00eaa54-e127-4722-9efb-f1120e704e72)

![image](https://github.com/user-attachments/assets/b05529a0-55d1-438c-9d2a-e916b6f90afa)

![image](https://github.com/user-attachments/assets/25540b45-4c6f-41ce-96ce-d219fbf9495a)










 






