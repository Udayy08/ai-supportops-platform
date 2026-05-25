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
  description = "Application URL via Nginx (K8s NodePort)"
  value       = "http://${aws_eip.supportops.public_ip}:30080"
}

output "api_url" {
  description = "Direct API URL"
  value       = "http://${aws_eip.supportops.public_ip}:8000"
}

output "health_check_url" {
  description = "Health check endpoint"
  value       = "http://${aws_eip.supportops.public_ip}:30080/health"
}

output "jenkins_ssh_tunnel" {
  description = "SSH tunnel command to access Jenkins (not publicly exposed)"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem -L 8082:localhost:30082 ubuntu@${aws_eip.supportops.public_ip}  # Then open http://localhost:8082"
}

output "kubeconfig_command" {
  description = "Command to copy kubeconfig from EC2 for remote kubectl access"
  value       = "scp -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.supportops.public_ip}:~/.kube/config ~/.kube/config-supportops"
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.supportops.id
}
