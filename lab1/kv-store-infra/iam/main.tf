# Milestone 1 (IaC). Read-only policy and a role that the IAM user "viewer" can assume.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "eu-north-1"
}

variable "viewer_user_name" {
  description = "Existing IAM user that is allowed to assume the role"
  type        = string
  default     = "viewer"
}

data "aws_caller_identity" "current" {}

# Policy: only Describe/Get/List actions, no write access
data "aws_iam_policy_document" "view_only" {
  statement {
    sid    = "ViewOnlyResources"
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "iam:Get*",
      "iam:List*",
      "s3:Get*",
      "s3:List*",
      "cloudformation:Describe*",
      "cloudformation:Get*",
      "cloudformation:List*",
      "cloudwatch:Describe*",
      "cloudwatch:Get*",
      "cloudwatch:List*",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "view_only" {
  name        = "ViewOnlyResourcesTF"
  description = "Allows only Describe/Get/List actions (no write access)"
  policy      = data.aws_iam_policy_document.view_only.json
}

# Trust policy: only the viewer user can assume the role
data "aws_iam_policy_document" "trust_viewer" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/${var.viewer_user_name}"]
    }
  }
}

resource "aws_iam_role" "view_only" {
  name               = "ViewOnlyRoleTF"
  description        = "Read-only role that can be assumed by the viewer user"
  assume_role_policy = data.aws_iam_policy_document.trust_viewer.json
}

resource "aws_iam_role_policy_attachment" "view_only" {
  role       = aws_iam_role.view_only.name
  policy_arn = aws_iam_policy.view_only.arn
}

output "policy_arn" {
  value = aws_iam_policy.view_only.arn
}

output "role_arn" {
  value = aws_iam_role.view_only.arn
}

output "switch_role_url" {
  value = "https://signin.aws.amazon.com/switchrole?account=${data.aws_caller_identity.current.account_id}&roleName=${aws_iam_role.view_only.name}"
}
