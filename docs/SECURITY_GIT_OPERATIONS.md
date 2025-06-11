# Git Operations Security Guide

## Overview
This document provides guidance on securely handling Git operations within containerized AI agents, particularly when using SSH keys for authentication.

## SSH Key Mounting

### Current Implementation
The system currently uses HTTPS URLs with personal access tokens for Git operations. This approach:
- ✅ Works seamlessly with non-root container users
- ✅ Requires no special file permissions
- ✅ Avoids SSH key permission issues

### SSH Key Support (Future Enhancement)
If SSH-based Git operations are required, consider the following implementation:

```python
# In code_task_v2.py container configuration
if use_ssh_git:
    ssh_dir = os.path.expanduser('~/.ssh')
    container_kwargs['volumes'].update({
        ssh_dir: {
            'bind': '/home/appuser/.ssh',
            'mode': 'ro'  # Read-only for security
        }
    })
    
    # Ensure SSH key permissions in container command
    container_command = f'''
    # Fix SSH permissions for non-root user
    mkdir -p ~/.ssh
    cp -r /home/appuser/.ssh/* ~/.ssh/ 2>/dev/null || true
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/id_* 2>/dev/null || true
    
    # Configure SSH to accept host keys automatically (for CI/CD)
    echo "StrictHostKeyChecking no" >> ~/.ssh/config
    
    {original_command}
    '''
```

### Security Considerations

1. **File Permissions**: SSH keys must have correct permissions (600) or SSH will reject them
2. **User Mapping**: Keys must be readable by UID 1000 (container user)
3. **Read-Only Mount**: Mount SSH directory as read-only to prevent key modification
4. **Host Key Verification**: Consider the security implications of disabling host key checking

### Recommended Approach

For maximum security and compatibility, we recommend continuing to use HTTPS with personal access tokens:

1. **Token Rotation**: Implement regular token rotation
2. **Minimal Scopes**: Use tokens with only necessary permissions (repo, write)
3. **Environment Variables**: Pass tokens via environment variables, not command arguments
4. **Token Cleanup**: Clear tokens from environment after use

### Implementation Example

```python
# Secure token handling
def setup_git_auth(container_kwargs, github_token):
    """Configure Git authentication securely."""
    # Use environment variable for token
    container_kwargs['environment']['GIT_TOKEN'] = github_token
    
    # Configure Git to use token
    git_config_cmd = '''
    git config --global credential.helper '!f() { echo "username=x-access-token"; echo "password=$GIT_TOKEN"; }; f'
    '''
    
    return git_config_cmd
```

### Troubleshooting SSH Issues

If SSH operations fail with permission errors:

1. **Check Container User**: Verify container runs as UID 1000
   ```bash
   docker exec <container> id
   ```

2. **Verify Key Permissions**: 
   ```bash
   docker exec <container> ls -la ~/.ssh/
   ```

3. **Test SSH Connection**:
   ```bash
   docker exec <container> ssh -T git@github.com
   ```

4. **Debug SSH**:
   ```bash
   docker exec <container> ssh -vvv git@github.com
   ```

### Migration Path

To migrate from HTTPS to SSH:

1. Update repository URLs in task configuration
2. Mount SSH keys with proper permissions
3. Add SSH configuration to container startup
4. Test with a non-critical repository first
5. Monitor for permission errors in logs