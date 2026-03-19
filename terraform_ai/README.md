# Terraform Plan Explainer

Analyzes `terraform plan` output using Claude AI and generates a human-readable explanation with risk analysis.

---

## Project structure

```
terraform_ai/
├── explainer.py          # Python script that sends the plan to Claude AI
├── requirements.txt      # Python dependencies
├── sample-plan.txt       # Sample plan for testing
└── terraform/
    ├── main.tf           # EC2 instance + S3 bucket
    ├── variables.tf      # Input variables
    └── outputs.tf        # Output values
```

---

## 1. Terraform — Provisioning EC2 + S3

### Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- AWS credentials configured (`aws configure` or environment variables)

### Resources created

| Resource | Description |
|---|---|
| `aws_instance.main` | Amazon Linux 2023 EC2 (t3.micro, encrypted EBS, IMDSv2) |
| `aws_s3_bucket.main` | S3 bucket with versioning, AES-256 encryption and public access blocked |
| `aws_security_group.ec2` | Security group (egress only) |

### Setup and plan

```bash
cd terraform

# Initialize providers
terraform init

# Preview changes (required before the AI analysis)
terraform plan -out=tfplan

# Export plan as readable text
terraform show -no-color tfplan > plan.txt
```

> **Tip:** pass `-var='bucket_name=your-unique-name-here'` to avoid conflicts,
> since S3 bucket names must be globally unique.

```bash
terraform plan -out=tfplan -var='bucket_name=mycompany-demo-2024'
terraform show -no-color tfplan > plan.txt
```

### Apply / Destroy

```bash
# Apply the plan
terraform apply tfplan

# Destroy all resources when done
terraform destroy
```

---

## 2. Python Explainer — AI analysis with Claude

### Setup

```bash
# From the terraform_ai/ root
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."
# or add it to a .env file:
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
```

### Analyze the Terraform plan

```bash
# Analyze from the exported plan file (recommended)
python explainer.py --file terraform/plan.txt

# In English
python explainer.py --file terraform/plan.txt --lang en

# Pipe directly from terraform show
terraform show -no-color terraform/tfplan | python explainer.py

# Quick test with the sample plan
python explainer.py --file sample-plan.txt
```

### End-to-end flow

```bash
# 1. Generate and export the plan
cd terraform
terraform init
terraform plan -out=tfplan -var='bucket_name=mycompany-demo-2024'
terraform show -no-color tfplan > plan.txt
cd ..

# 2. Analyze with Claude AI
python explainer.py --file terraform/plan.txt
```

---

## Example output

```
🔍 Analyzing Terraform plan...

────────────────────────────────────────────────────────────

## Summary
This plan creates an EC2 instance (Amazon Linux 2023 / t3.micro) and an S3 bucket
with versioning and server-side encryption enabled. No destructive operations are planned.

## Changes by Resource
- ✅ CREATE: aws_s3_bucket.main
- ✅ CREATE: aws_s3_bucket_versioning.main
- ✅ CREATE: aws_s3_bucket_server_side_encryption_configuration.main
- ✅ CREATE: aws_s3_bucket_public_access_block.main
- ✅ CREATE: aws_security_group.ec2
- ✅ CREATE: aws_instance.main

## Risk Analysis
- **[LOW]** aws_instance.main: New EC2 instance — verify instance type and subnet before applying.
- **[LOW]** aws_s3_bucket.main: Bucket name must be globally unique; plan will fail if already taken.

## Recommendation
**SAFE TO APPLY** — All operations are additive. Confirm bucket name uniqueness and AWS costs before proceeding.

────────────────────────────────────────────────────────────
```
