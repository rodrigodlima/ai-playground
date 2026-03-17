# Terraform Plan Explainer

Analyzes `terraform plan` output using Claude AI and generates a human-readable explanation with risk analysis.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

```bash
# Pipe directly from terraform
terraform plan | python explainer.py

# From a file
python explainer.py --file plan.txt

# In English
python explainer.py --file plan.txt --lang en

# Recommended flow (saved plan + explain)
terraform plan -out=tfplan
terraform show -no-color tfplan | python explainer.py
```

## Example output

```
🔍 Analyzing Terraform plan...

────────────────────────────────────────────────────────────

## Summary
This plan creates the base infrastructure on Azure (resource group and VNet),
updates the application subnet address, and performs high-risk operations
on the PostgreSQL database and Key Vault.

## 🔄 Changes by Resource
- ✅ CREATE: azurerm_resource_group.main
- ✅ CREATE: azurerm_virtual_network.main
- 🔁 UPDATE: azurerm_subnet.app — address prefix change
- ⚠️  REPLACE: azurerm_key_vault_secret.db_password — rename forces recreation
- 🔴 DESTROY: azurerm_postgresql_flexible_server.main

##  Risk Analysis
- **[HIGH]** azurerm_postgresql_flexible_server.main: Destruction of production PostgreSQL server. Data will be lost if there is no backup.
- **[HIGH]** azurerm_key_vault_secret.db_password: Secret replacement — applications depending on the old name will break.
- **[MEDIUM]** azurerm_subnet.app: CIDR change may affect existing routes and NSGs.

##  Recommendation
**DO NOT APPLY** — Destruction of the production database with no evidence of migration or backup. Review before proceeding.

────────────────────────────────────────────────────────────
```

## Testing with the sample

```bash
python explainer.py --file sample-plan.txt
```
