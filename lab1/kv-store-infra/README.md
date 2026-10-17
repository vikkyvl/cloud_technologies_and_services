# kv-store-infra

Infrastructure as Code for the Cloud Architectures capstone (Milestone 1, extended level).
Provider: AWS, region `eu-north-1` (Europe, Stockholm). Tool: Terraform.

## Structure

| Folder | What it creates |
|---|---|
| `iam/` | Read-only managed policy `ViewOnlyResourcesTF` and role `ViewOnlyRoleTF` that the IAM user `viewer` can assume |
| `network/` | VPC `kv-store-tf-vpc` (10.2.0.0/16) with a public subnet (Internet Gateway) and a private subnet (local route only), no NAT Gateway |

## Usage

```bash
cd iam          # or: cd network
terraform init
terraform plan
terraform apply
```

To remove everything created by a folder:

```bash
terraform destroy
```

All resources are free of charge (IAM, VPC, subnets, route tables, Internet Gateway).
