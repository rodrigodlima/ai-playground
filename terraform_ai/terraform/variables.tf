variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
  default     = "demo-ec2"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "bucket_name" {
  description = "Globally unique name for the S3 bucket"
  type        = string
  # Override this with a unique name, e.g.: terraform apply -var='bucket_name=mycompany-demo-2024'
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    Project     = "terraform-ai-demo"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}
