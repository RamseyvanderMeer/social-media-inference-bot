#!/usr/bin/env python3
"""Test and validate Docker setup configuration."""

import os
import subprocess
import sys
from pathlib import Path

def check_docker_installed():
    """Check if Docker is installed."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "Docker command failed"
    except FileNotFoundError:
        return False, "Docker not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "Docker command timed out"
    except Exception as e:
        return False, f"Error checking Docker: {str(e)}"

def check_docker_compose_installed():
    """Check if Docker Compose is installed."""
    try:
        # Try docker compose (v2)
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip(), "v2"
    except:
        pass
    
    try:
        # Try docker-compose (v1)
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip(), "v1"
    except:
        pass
    
    return False, "Docker Compose not found", None

def check_docker_running():
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "Docker daemon is running"
        return False, "Docker daemon is not running"
    except Exception as e:
        return False, f"Cannot connect to Docker daemon: {str(e)}"

def check_files():
    """Check if all required Docker files exist."""
    required_files = {
        "Dockerfile": "Container definition",
        "docker-compose.yml": "Docker Compose configuration",
        "docker-entrypoint.sh": "Container entrypoint script",
        ".dockerignore": "Build exclusions",
        ".env.example": "Environment template",
    }
    
    results = {}
    for file, description in required_files.items():
        path = Path(file)
        exists = path.exists()
        results[file] = {
            "exists": exists,
            "description": description,
            "size": path.stat().st_size if exists else 0,
        }
    
    return results

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    if not env_path.exists():
        return False, ".env file does not exist", []
    
    required_vars = ["GROK_API_KEY", "OPENAI_API_KEY"]
    found_vars = []
    missing_vars = []
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
            for var in required_vars:
                if f"{var}=" in content:
                    # Check if it's not just a placeholder
                    lines = content.split("\n")
                    for line in lines:
                        if line.startswith(f"{var}="):
                            value = line.split("=", 1)[1].strip()
                            if value and value != f"your_{var.lower()}_here" and "your_" not in value.lower():
                                found_vars.append(var)
                                break
                    else:
                        missing_vars.append(var)
                else:
                    missing_vars.append(var)
    except Exception as e:
        return False, f"Error reading .env file: {str(e)}", []
    
    if missing_vars:
        return False, f"Missing or placeholder values for: {', '.join(missing_vars)}", found_vars
    return True, "All required variables found", found_vars

def validate_dockerfile():
    """Basic validation of Dockerfile."""
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        return False, "Dockerfile not found", []
    
    issues = []
    try:
        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()
            
            # Check for required elements
            if "FROM python:3.12" not in content:
                issues.append("Base image should be python:3.12")
            if "WORKDIR /app" not in content:
                issues.append("Missing WORKDIR /app")
            if "COPY requirements.txt" not in content:
                issues.append("Missing requirements.txt copy")
            if "docker-entrypoint.sh" not in content:
                issues.append("Missing docker-entrypoint.sh reference")
    except Exception as e:
        return False, f"Error reading Dockerfile: {str(e)}", []
    
    if issues:
        return False, "Dockerfile validation issues found", issues
    return True, "Dockerfile looks good", []

def validate_docker_compose():
    """Basic validation of docker-compose.yml."""
    compose_path = Path("docker-compose.yml")
    if not compose_path.exists():
        return False, "docker-compose.yml not found", []
    
    issues = []
    try:
        with open(compose_path, "r", encoding="utf-8") as f:
            content = f.read()
            
            if "GROK_API_KEY" not in content:
                issues.append("Missing GROK_API_KEY in environment")
            if "OPENAI_API_KEY" not in content:
                issues.append("Missing OPENAI_API_KEY in environment")
            if "./data:/app/data" not in content:
                issues.append("Missing data volume mount")
    except Exception as e:
        return False, f"Error reading docker-compose.yml: {str(e)}", []
    
    if issues:
        return False, "docker-compose.yml validation issues found", issues
    return True, "docker-compose.yml looks good", []

def print_installation_instructions():
    """Print Docker installation instructions for Windows."""
    print("\n" + "=" * 80)
    print("DOCKER INSTALLATION INSTRUCTIONS FOR WINDOWS")
    print("=" * 80)
    print("""
1. Download Docker Desktop for Windows:
   https://www.docker.com/products/docker-desktop/

2. Install Docker Desktop:
   - Run the installer
   - Follow the installation wizard
   - Restart your computer if prompted

3. Start Docker Desktop:
   - Launch Docker Desktop from Start menu
   - Wait for it to start (whale icon in system tray)

4. Verify installation:
   - Open PowerShell or Command Prompt
   - Run: docker --version
   - Run: docker-compose --version

5. After installation, run this script again to test the setup.
""")

def main():
    """Main test function."""
    print("=" * 80)
    print("DOCKER SETUP VALIDATION")
    print("=" * 80)
    print()
    
    all_checks_passed = True
    
    # Check Docker installation
    print("1. Checking Docker installation...")
    docker_installed, docker_info = check_docker_installed()
    if docker_installed:
        print(f"   [OK] Docker installed: {docker_info}")
        
        # Check if Docker is running
        docker_running, docker_status = check_docker_running()
        if docker_running:
            print(f"   [OK] {docker_status}")
        else:
            print(f"   [FAIL] {docker_status}")
            all_checks_passed = False
            print("   -> Start Docker Desktop and try again")
    else:
        print(f"   [FAIL] {docker_info}")
        all_checks_passed = False
        print_installation_instructions()
        print("\nContinuing with configuration file validation...\n")
    
    print()
    
    # Check Docker Compose
    print("2. Checking Docker Compose...")
    compose_installed, compose_info, compose_version = check_docker_compose_installed()
    if compose_installed:
        print(f"   [OK] Docker Compose installed ({compose_version}): {compose_info}")
    else:
        print(f"   [FAIL] {compose_info}")
        all_checks_passed = False
    
    print()
    
    # Check required files
    print("3. Checking required files...")
    files = check_files()
    for file, info in files.items():
        if info["exists"]:
            print(f"   [OK] {file} ({info['size']} bytes) - {info['description']}")
        else:
            print(f"   [FAIL] {file} - {info['description']} - MISSING")
            all_checks_passed = False
    
    print()
    
    # Validate Dockerfile
    print("4. Validating Dockerfile...")
    dockerfile_ok, dockerfile_msg, dockerfile_issues = validate_dockerfile()
    if dockerfile_ok:
        print(f"   [OK] {dockerfile_msg}")
    else:
        print(f"   [FAIL] {dockerfile_msg}")
        for issue in dockerfile_issues:
            print(f"     - {issue}")
        all_checks_passed = False
    
    print()
    
    # Validate docker-compose.yml
    print("5. Validating docker-compose.yml...")
    compose_ok, compose_msg, compose_issues = validate_docker_compose()
    if compose_ok:
        print(f"   [OK] {compose_msg}")
    else:
        print(f"   [FAIL] {compose_msg}")
        for issue in compose_issues:
            print(f"     - {issue}")
        all_checks_passed = False
    
    print()
    
    # Check .env file
    print("6. Checking .env file...")
    env_ok, env_msg, env_vars = check_env_file()
    if env_ok:
        print(f"   [OK] {env_msg}")
        print(f"     Found variables: {', '.join(env_vars)}")
    else:
        print(f"   [FAIL] {env_msg}")
        if "does not exist" in env_msg:
            print("   -> Create .env file from .env.example and add your API keys")
        all_checks_passed = False
    
    print()
    print("=" * 80)
    
    if all_checks_passed:
        print("[SUCCESS] ALL CHECKS PASSED!")
        print()
        print("You can now build and run the Docker container:")
        print("  docker-compose build")
        print("  docker-compose up")
    else:
        print("[WARNING] SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before building the Docker container.")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
