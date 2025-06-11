# Container Permission Troubleshooting Guide

## Overview
This guide helps diagnose and resolve permission-related issues when running AI agents in containers.

## Common Permission Issues

### 1. Container Cannot Write to Workspace

**Symptoms:**
- `Permission denied` errors when creating files
- `touch: cannot touch '/workspace/file': Permission denied`
- Git operations fail with permission errors

**Diagnosis:**
```bash
# Check container user
docker exec <container-id> id

# Check workspace permissions
docker exec <container-id> ls -la /workspace

# Check volume mount permissions
docker inspect <container-id> | grep -A 10 Mounts
```

**Solutions:**

1. **Verify UID/GID Configuration**
   ```bash
   # Check configured values
   echo "CONTAINER_UID=${CONTAINER_UID:-1000}"
   echo "CONTAINER_GID=${CONTAINER_GID:-1000}"
   
   # Rebuild with custom UID/GID if needed
   docker build --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g) \
     -f Dockerfile.claude-automation -t claude-code-automation:latest .
   ```

2. **Fix Workspace Permissions**
   ```bash
   # Manually fix permissions
   sudo chown -R 1000:1000 /tmp/ai-workspace-*
   
   # Or use your current user
   sudo chown -R $(id -u):$(id -g) /tmp/ai-workspace-*
   ```

3. **Use Environment Variables**
   ```bash
   # Set custom UID/GID
   export CONTAINER_UID=$(id -u)
   export CONTAINER_GID=$(id -g)
   
   # Restart the service
   docker-compose restart
   ```

### 2. Git SSH Key Permission Errors

**Symptoms:**
- `WARNING: UNPROTECTED PRIVATE KEY FILE!`
- `Permission denied (publickey)`
- `Host key verification failed`

**Solutions:**

1. **Fix SSH Key Permissions**
   ```bash
   # On host system
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/id_*
   chmod 644 ~/.ssh/*.pub
   ```

2. **Use HTTPS Instead of SSH**
   ```bash
   # Convert SSH URL to HTTPS
   git remote set-url origin https://github.com/user/repo.git
   ```

3. **Mount SSH Directory Correctly**
   ```python
   # In code_task_v2.py
   container_kwargs['volumes'].update({
       os.path.expanduser('~/.ssh'): {
           'bind': '/home/appuser/.ssh',
           'mode': 'ro'
       }
   })
   ```

### 3. Container Cannot Execute Commands

**Symptoms:**
- `Operation not permitted`
- `Cannot execute binary file`
- `Permission denied` when running scripts

**Diagnosis:**
```bash
# Check security options
docker inspect <container-id> | grep -A 5 SecurityOpt

# Check capabilities
docker exec <container-id> capsh --print
```

**Solutions:**

1. **Verify Security Options**
   ```bash
   # Should see: "no-new-privileges=true"
   # Should NOT see: "privileged=true" or "seccomp=unconfined"
   ```

2. **Check Binary Permissions**
   ```bash
   docker exec <container-id> ls -la /usr/local/bin/
   ```

### 4. Workspace Not Accessible

**Symptoms:**
- `/tmp/ai-workspace-*: No such file or directory`
- Volume mount fails
- Container cannot access mounted directories

**Solutions:**

1. **Verify Workspace Creation**
   ```bash
   # Check if workspace exists
   ls -la /tmp/ai-workspace-*
   
   # Check ownership
   stat /tmp/ai-workspace-*
   ```

2. **Check SELinux/AppArmor**
   ```bash
   # For SELinux systems
   ls -Z /tmp/ai-workspace-*
   
   # May need to add :z flag to volume mount
   volumes:
     /tmp/ai-workspace-123: /workspace:z
   ```

## Debugging Commands

### Container Inspection
```bash
# Full container configuration
docker inspect <container-id>

# Security configuration
docker inspect <container-id> | jq '.[0].HostConfig.SecurityOpt'

# User configuration
docker exec <container-id> id

# Environment variables
docker exec <container-id> env | grep -E 'UID|GID|USER'
```

### File System Checks
```bash
# Check mounted volumes
docker exec <container-id> mount | grep workspace

# Check file permissions
docker exec <container-id> find /workspace -type f -ls

# Check directory permissions
docker exec <container-id> find /workspace -type d -ls
```

### Process Checks
```bash
# Check running processes
docker exec <container-id> ps aux

# Check process capabilities
docker exec <container-id> cat /proc/self/status | grep Cap
```

## Prevention Strategies

1. **Use Configuration Management**
   ```bash
   # .env file
   CONTAINER_UID=1000
   CONTAINER_GID=1000
   WORKSPACE_BASE_PATH=/var/lib/async-code/workspaces
   ```

2. **Implement Health Checks**
   ```python
   def check_container_permissions(container_id):
       """Verify container has correct permissions."""
       result = docker_client.containers.get(container_id).exec_run(
           "touch /workspace/test && rm /workspace/test"
       )
       return result.exit_code == 0
   ```

3. **Add Logging**
   ```python
   logger.info(f"Container user: {get_container_user_mapping()}")
   logger.info(f"Workspace path: {workspace_path}")
   logger.info(f"Security options: {get_security_options()}")
   ```

## Emergency Fixes

### Reset All Permissions
```bash
#!/bin/bash
# reset-permissions.sh

# Stop all containers
docker stop $(docker ps -q --filter "name=ai-code-task-")

# Clean up workspaces
sudo rm -rf /tmp/ai-workspace-*

# Rebuild images
docker build -f Dockerfile.claude-automation -t claude-code-automation:latest .
docker build -f Dockerfile.codex-automation -t codex-automation:latest .

# Restart services
docker-compose down
docker-compose up -d
```

### Force Container Cleanup
```bash
# Remove all AI task containers
docker rm -f $(docker ps -a -q --filter "name=ai-code-task-")

# Clean up volumes
docker volume prune -f
```

## Getting Help

If issues persist:

1. **Collect Debug Information**
   ```bash
   docker version
   docker info
   uname -a
   id
   ls -la /tmp/ai-workspace-*
   ```

2. **Check Logs**
   ```bash
   docker logs <container-id>
   docker-compose logs server
   ```

3. **File an Issue**
   Include:
   - Error messages
   - Debug information
   - Steps to reproduce
   - Environment details