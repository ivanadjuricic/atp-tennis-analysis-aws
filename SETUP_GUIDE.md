# 🚀 Setup & Deployment Guide

This guide explains how to replicate this project in your own AWS environment.

## Prerequisites

- AWS Account with Lambda, S3, and EventBridge access
- Kaggle account with API credentials
- Basic knowledge of AWS Console
- Python 3.12 installed locally (for testing)

---

## Step 1: Get Kaggle API Credentials

1. Go to [kaggle.com/account](https://www.kaggle.com/account)
2. Scroll to **API** section
3. Click **"Create New API Token"**
4. Download `kaggle.json` file
5. Note your `username` and `key` values

⚠️ **Keep these credentials secure! Never commit them to Git.**

---

## Step 2: Create S3 Bucket

1. Go to **AWS S3 Console**
2. Click **"Create bucket"**
3. Bucket name: `atp-analysis-task` (or your preferred name)
4. Region: `eu-north-1` (or your preferred region)
5. Leave other settings as default
6. Click **"Create bucket"**

---

## Step 3: Create IAM Role for Lambda

1. Go to **AWS IAM Console** → **Roles** → **Create role**
2. Select **AWS service** → **Lambda**
3. Attach policies:
   - `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
   - `AmazonS3FullAccess` (for S3 operations)
4. Role name: `lambda-atp-analysis-role`
5. Click **"Create role"**

**Security Best Practice:** For production, restrict S3 policy to specific bucket only.

---

## Step 4: Create Lambda Layers

### Layer 1: AWS Pandas Layer (Managed)

1. Go to **Lambda Console** → **Layers** → **Add layer**
2. Select **AWS layers**
3. Choose **AWSSDKPandas-Python312**
4. Version: Latest (currently 12)

### Layer 2: Custom Kaggle Layer (Docker Build)

**Option A: Use Docker (Recommended)**

```bash
# Create directory
mkdir kaggle-layer && cd kaggle-layer

# Create requirements.txt
echo "kaggle==1.5.13" > requirements.txt

# Build layer using AWS Lambda Python 3.12 image
docker run --platform linux/amd64 \
  -v $(pwd):/var/task \
  public.ecr.aws/lambda/python:3.12 \
  pip install -r requirements.txt -t python/

# Create ZIP file
zip -r kaggle-layer.zip python/

# Upload to AWS Lambda Layers via Console
```

## Step 5: Create Lambda Function

1. Go to **Lambda Console** → **Create function**
2. Function name: `atp-analysis-function`
3. Runtime: **Python 3.12**
4. Architecture: **x86_64**
5. Execution role: Use existing `lambda-atp-analysis-role`
6. Click **"Create function"**

### Configure Function Settings

**Memory:** 512 MB  
**Timeout:** 5 minutes (300 seconds)

**Add Layers:**
- AWSSDKPandas-Python312 (version 12)
- kaggle-layer (your custom layer)

**Environment Variables:**
```
KAGGLE_USERNAME = your_kaggle_username
KAGGLE_KEY = your_kaggle_api_key
```

**Copy Code:**
Upload `src/lambda_function.py` from this repository.

---

## Step 6: Create EventBridge Rule

1. Go to **EventBridge Console** → **Rules** → **Create rule**
2. Name: `atp-weekly-trigger`
3. Rule type: **Schedule**
4. Schedule pattern: **Cron expression**
   ```
   cron(0 6 ? * MON *)
   ```
   (Every Monday at 06:00 UTC)
5. Target: **Lambda function** → Select `atp-analysis-function`
6. Click **"Create"**

---

## Step 7: Test the Function

1. Go to **Lambda Console** → `atp-analysis-function`
2. Click **"Test"** → **Create new test event**
3. Event name: `ManualTest`
4. Use default event JSON: `{}`
5. Click **"Test"**

**Expected Result:**
- Execution succeeds
- CloudWatch logs show Kaggle download progress
- CSV file appears in S3 bucket: `results/atp-top-50-{date}.csv`

---

## Step 8: Monitor Execution

**CloudWatch Logs:**
- Go to **CloudWatch Console** → **Log groups**
- Find `/aws/lambda/atp-analysis-function`
- View execution logs

**S3 Output:**
- Go to **S3 Console** → `atp-analysis-task` bucket
- Navigate to `results/` folder
- Download CSV to verify data

---

## Troubleshooting

### Issue: "No module named 'kaggle'"
**Solution:** Ensure Kaggle layer is attached and version is correct.

### Issue: "Could not find kaggle.json"
**Solution:** Check environment variables are set correctly in Lambda.

### Issue: Lambda timeout
**Solution:** Increase timeout to 5 minutes and memory to 512 MB.

### Issue: Permission denied on S3
**Solution:** Verify IAM role has S3 write permissions.

---

## Cost Estimation

**Monthly Cost (approximate):**
- Lambda: $0.20 (4 executions/month, 5 sec each)
- S3: $0.03 (storage for CSV files)
- EventBridge: Free (included in Free Tier)
- CloudWatch Logs: $0.50 (minimal logging)

**Total:** ~$0.75/month

---

## Security Checklist

- [ ] Kaggle credentials stored as environment variables
- [ ] IAM role follows least-privilege principle
- [ ] S3 bucket has appropriate access controls
- [ ] CloudWatch logs enabled for monitoring
- [ ] No secrets committed to Git repository
- [ ] API keys rotated regularly

---

## Next Steps

1. Test manual execution
2. Wait for scheduled EventBridge trigger (Monday 06:00 UTC)
3. Verify automated execution in CloudWatch
4. Check S3 for new CSV file
5. Implement monitoring enhancements (CloudWatch Alarms, SNS notifications)

---

## Questions?

If you encounter issues, check:
1. CloudWatch Logs for detailed error messages
2. IAM role permissions
3. Lambda layer compatibility (Python version)
4. Environment variable configuration

---

**Happy deploying!** 🚀
