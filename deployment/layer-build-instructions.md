# Kaggle Lambda Layer - Build Instructions

## Overview

This document explains how I created a custom Kaggle Lambda layer for AWS Lambda using Docker Desktop. The resulting layer (93 MB) was uploaded to AWS Lambda Layers and is **not included in this repository** due to file size constraints.

## Why a Custom Layer Was Needed

AWS Lambda runs on **Amazon Linux 2** (Linux OS), but I developed on **Windows**. Python packages built on Windows contain Windows-specific binaries (`.pyd` files) that are incompatible with Linux.

**Solution:** Use Docker to build the Kaggle package in a Linux environment that matches AWS Lambda's runtime.

---

## Build Process

### Step 1: Create Folder Structure

Created a folder named `kaggle-layer` with the following structure:

```
kaggle-layer/
└── python/
    └── (Kaggle package will be installed here)
```

**Important:** The `python/` folder name is required by AWS Lambda. Lambda automatically adds `/opt/python` to the Python path, so packages must be in a folder named `python/`.

---

### Step 2: Use Docker Desktop to Build Layer

Opened **Command Prompt** in the directory containing `kaggle-layer/` folder and ran:

```bash
docker run --platform linux/amd64 -v "%cd%/kaggle-layer:/var/task" public.ecr.aws/lambda/python:3.12 pip install kaggle -t python/
```

**Command Breakdown:**
- `docker run` - Runs a Docker container
- `--platform linux/amd64` - Specifies Linux AMD64 architecture (matches AWS Lambda)
- `-v "%cd%/kaggle-layer:/var/task"` - Mounts local `kaggle-layer` folder into container's `/var/task` directory
- `public.ecr.aws/lambda/python:3.12` - Uses official AWS Lambda Python 3.12 base image
- `pip install kaggle -t python/` - Installs Kaggle package into `python/` folder with all dependencies

**Output:** Docker downloaded the AWS Lambda Python 3.12 image and installed Kaggle with all dependencies into `kaggle-layer/python/`

---

### Step 3: Verify Installation

Checked `kaggle-layer/python/` folder and confirmed it contains:

```
kaggle-layer/
└── python/
    ├── kaggle/               ← Main Kaggle library
    ├── certifi/              ← Dependency
    ├── charset_normalizer/   ← Dependency
    ├── click/                ← Dependency
    ├── dateutil/             ← Dependency
    ├── idna/                 ← Dependency
    ├── urllib3/              ← Dependency
    ├── six.py                ← Dependency
    ├── tqdm/                 ← Dependency
    ├── slugify/              ← Dependency
    └── (other dependencies)
```

**Total Size:** ~93 MB (uncompressed)

---

### Step 4: Create ZIP File

**Right-click** on `kaggle-layer` folder → **Send to** → **Compressed (zipped) folder**

This created `kaggle-layer.zip` with the following structure:

```
kaggle-layer.zip
└── python/
    ├── kaggle/
    ├── certifi/
    ├── charset_normalizer/
    └── ...
```

**Critical:** The ZIP must have `python/` at the root level, NOT `kaggle-layer/python/`.

**Verification:**
- Opened ZIP file
- Confirmed `python/` folder is at the root
- Confirmed all dependencies are inside `python/`

---

### Step 5: Upload to AWS Lambda Layers

1. Navigated to **AWS Lambda Console** (eu-north-1 region)
2. Clicked **Layers** → **Create layer**
3. Configured layer:
   - **Name:** `kaggle-layer`
   - **Upload:** Selected `kaggle-layer.zip` (93 MB)
   - **Compatible runtimes:** Python 3.12
   - **Compatible architectures:** x86_64
4. Clicked **Create**

**Result:**
- Layer created successfully
- **ARN:** `arn:aws:lambda:eu-north-1:616421593302:layer:kaggle-layer:1`
- **Version:** 1

---

### Step 6: Attach Layer to Lambda Function

1. Opened **AWS Lambda Console** → `atp-analysis-function`
2. Clicked **Configuration** tab → **Layers**
3. Clicked **Add a layer**
4. Selected **Custom layers** → `kaggle-layer` → Version 1
5. Clicked **Add**

**Also attached AWS managed layer:**
- **AWSSDKPandas-Python312** (Version 12)
- ARN: `arn:aws:lambda:eu-north-1:336392948345:layer:AWSSDKPandas-Python312:12`

**Final Configuration:**
Lambda function now has access to:
- ✅ `kaggle` library (custom layer - 93 MB)
- ✅ `pandas`, `numpy`, `boto3` (AWS managed layer)

---

## Testing the Layer

Verified layer works by running Lambda function with this test code:

```python
import kaggle
import pandas as pd

print(f"Kaggle version: {kaggle.__version__}")
print(f"Pandas version: {pd.__version__}")
```

**Output:**
```
Kaggle version: 1.8.3
Pandas version: 2.0.3
```

✅ Both libraries imported successfully!

---

## Why This Approach Works

| Aspect | Explanation |
|--------|-------------|
| **Cross-platform compatibility** | Docker builds packages in Linux environment matching AWS Lambda |
| **Correct Python version** | Uses exact Python 3.12 runtime that Lambda uses |
| **All dependencies included** | Kaggle's dependencies (certifi, urllib3, tqdm, etc.) automatically installed |
| **Proper folder structure** | `python/` folder name ensures Lambda can find packages |

---

## Alternative Methods (If You Don't Have Docker)

### Option 1: AWS Cloud9
1. Create Cloud9 environment (runs on Amazon Linux 2)
2. Run: `mkdir -p kaggle-layer/python`
3. Run: `pip install kaggle -t kaggle-layer/python/`
4. Zip and upload

### Option 2: EC2 Instance
1. Launch EC2 with Amazon Linux 2
2. SSH into instance
3. Build layer using same commands as Cloud9
4. Download ZIP and upload to Lambda Layers

### Option 3: AWS CloudShell
1. Open CloudShell in AWS Console
2. Build layer directly in CloudShell
3. Upload to Lambda Layers from CloudShell

---

## Troubleshooting

### Issue: "No module named 'kaggle'" in Lambda
**Cause:** ZIP structure incorrect (missing `python/` folder at root)  
**Solution:** Re-create ZIP ensuring `python/` is at root level, not nested

### Issue: Import errors for Kaggle dependencies
**Cause:** Dependencies not installed or wrong Python version  
**Solution:** Rebuild layer using `public.ecr.aws/lambda/python:3.12` image

### Issue: Layer size exceeds 250 MB (unzipped)
**Cause:** Too many packages or large dependencies  
**Solution:** AWS Lambda has 250 MB limit for unzipped layers (Kaggle layer is 93 MB, within limit)

---

## Layer Details

**Layer Name:** kaggle-layer  
**Version:** 1  
**Size:** 93 MB (zipped)  
**ARN:** `arn:aws:lambda:eu-north-1:616421593302:layer:kaggle-layer:1`  
**Compatible Runtimes:** Python 3.12  
**Architecture:** x86_64  
**Region:** eu-north-1 (Stockholm)  

---

## Important Notes

⚠️ **The `kaggle-layer.zip` file (93 MB) is NOT included in this repository** due to GitHub file size constraints (100 MB limit).

⚠️ **To replicate this project:** Follow the Docker build instructions above to create your own layer.

✅ **Layer ARN is documented** in the project report for reference.

---

## Dependencies Installed

The layer includes these packages (installed automatically with Kaggle):

```
kaggle==1.8.3
certifi==2026.1.4
charset-normalizer==3.4.4
click==8.3.1
python-dateutil
idna==3.11
urllib3
six
tqdm
python-slugify
bleach
requests
```

All dependencies are Linux-compatible and work correctly in AWS Lambda Python 3.12 runtime.

---

## What I Learned

- ✅ How to use Docker for cross-platform Python package building
- ✅ Understanding AWS Lambda layer structure requirements
- ✅ Difference between Windows and Linux Python package binaries
- ✅ AWS Lambda runtime environments and compatibility
- ✅ Layer size limits and optimization strategies

## Dependencies

See root `requirements.txt` for all project dependencies.

For building the Kaggle layer, only `kaggle>=1.5.13` is needed.

---

**Last Updated:** January 31, 2026  
**Created By:** Ivana Đuričić
