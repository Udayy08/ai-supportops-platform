# ─────────────────────────────────────────────────────────────────────────────
# AI SupportOps — Terraform Configuration
# EC2 + Elastic IP + k3s (Lightweight Kubernetes)
# ─────────────────────────────────────────────────────────────────────────────

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
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ai-supportops"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Data Sources
# ─────────────────────────────────────────────────────────────────────────────

# Latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Security Group
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_security_group" "supportops" {
  name        = "${var.project_name}-sg"
  description = "Security group for AI SupportOps EC2 instance"

  # SSH
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidr
  }

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Backend API (direct access for testing)
  ingress {
    description = "FastAPI Backend"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Nginx proxy (legacy docker-compose port)
  ingress {
    description = "Nginx Proxy"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # K8s NodePort — Nginx (app entry point via Kubernetes)
  ingress {
    description = "K8s Nginx NodePort"
    from_port   = 30080
    to_port     = 30080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # K8s API server — restricted to SSH-allowed IPs only
  ingress {
    description = "K8s API (restricted)"
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidr
  }

  # NOTE: Jenkins (port 8082) is intentionally NOT exposed.
  # Jenkins runs as a K8s ClusterIP service, accessible only via SSH tunnel:
  #   ssh -L 8082:localhost:30082 ubuntu@<ELASTIC_IP>

  # All outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# EC2 Instance
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_instance" "supportops" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.supportops.id]

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    # ── System updates ─────────────────────────────────────────────────────
    apt-get update -y
    apt-get upgrade -y

    # ── Install Docker ─────────────────────────────────────────────────────
    apt-get install -y ca-certificates curl gnupg lsb-release

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
      gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io \
      docker-buildx-plugin docker-compose-plugin

    # ── Enable Docker for ubuntu user ──────────────────────────────────────
    usermod -aG docker ubuntu

    # ── Install Git ────────────────────────────────────────────────────────
    apt-get install -y git

    # ── Create app directory ───────────────────────────────────────────────
    mkdir -p /home/ubuntu/app
    chown ubuntu:ubuntu /home/ubuntu/app

    # ── Start Docker ───────────────────────────────────────────────────────
    systemctl enable docker
    systemctl start docker

    # ── Install k3s (Lightweight Kubernetes) ───────────────────────────────
    # k3s includes: kubectl, containerd, CoreDNS, Traefik, local-path-provisioner
    # Using Docker as the container runtime since we already have it installed
    curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--docker" sh -

    # ── Wait for k3s to be ready ───────────────────────────────────────────
    echo "⏳ Waiting for k3s to be ready..."
    for i in $(seq 1 60); do
        if kubectl get nodes 2>/dev/null | grep -q " Ready"; then
            echo "✅ k3s is ready!"
            break
        fi
        if [ $i -eq 60 ]; then
            echo "❌ k3s did not become ready in time"
            exit 1
        fi
        sleep 5
    done

    # ── Configure kubectl for ubuntu user ──────────────────────────────────
    mkdir -p /home/ubuntu/.kube
    cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
    chown -R ubuntu:ubuntu /home/ubuntu/.kube
    chmod 600 /home/ubuntu/.kube/config

    # Allow ubuntu user to use kubectl without sudo
    echo 'export KUBECONFIG=/home/ubuntu/.kube/config' >> /home/ubuntu/.bashrc

    # ── Create K8s namespace ───────────────────────────────────────────────
    kubectl create namespace supportops || true

    echo "✅ EC2 bootstrap complete (Docker + k3s)" >> /home/ubuntu/setup.log
  EOF

  tags = {
    Name = "${var.project_name}-server"
  }
}

# ─────────────────────────────────────────────────────────────────────────────
# Elastic IP
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_eip" "supportops" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }
}

resource "aws_eip_association" "supportops" {
  instance_id   = aws_instance.supportops.id
  allocation_id = aws_eip.supportops.id
}
