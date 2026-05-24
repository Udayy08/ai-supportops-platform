# ─────────────────────────────────────────────────────────────────────────────
# AI SupportOps — Terraform Outputs
# ─────────────────────────────────────────────────────────────────────────────

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.supportops.id
}

output "elastic_ip" {
  description = "Elastic IP address (use this to access your app)"
  value       = aws_eip.supportops.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.supportops.public_ip}"
}

output "app_url" {
  description = "Application URL via Nginx"
  value       = "http://${aws_eip.supportops.public_ip}:8080"
}

output "api_url" {
  description = "Direct API URL"
  value       = "http://${aws_eip.supportops.public_ip}:8000"
}

output "health_check_url" {
  description = "Health check endpoint"
  value       = "http://${aws_eip.supportops.public_ip}:8000/health"
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.supportops.id
}
