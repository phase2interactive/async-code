# Task: Remove Excessive Docker Privileges

**Priority**: CRITICAL
**Component**: Backend - server/utils/code_task_v2.py
**Security Impact**: High - Host system compromise

## Problem
Docker containers run with excessive privileges that could allow container escape and host compromise.

## Current Dangerous Settings
```python
container = client.containers.run(
    privileged=True,
    cap_add=['ALL'],
    pid_mode='host',
    security_opt=['seccomp=unconfined']
)
```

## Required Changes

1. **Remove privileged mode**
   - Set `privileged=False`
   - Remove `cap_add=['ALL']`
   - Remove `pid_mode='host'`

2. **Use minimal capabilities**
   - Only add specific required capabilities
   - For git operations: `cap_add=['CHOWN', 'DAC_OVERRIDE']`

3. **Enable seccomp filtering**
   - Remove `seccomp=unconfined`
   - Use default seccomp profile

4. **Add security constraints**
   - Set memory limits
   - Set CPU limits
   - Use read-only root filesystem where possible

## Implementation Steps
1. Remove all privileged settings from container creation
2. Test which minimal capabilities are actually needed
3. Implement resource limits
4. Add security options for defense in depth
5. Update both claude and codex container configurations

## Acceptance Criteria
- [ ] Containers run without privileged mode
- [ ] Only minimal required capabilities are granted
- [ ] Resource limits prevent DoS attacks
- [ ] Containers cannot access host system
- [ ] All agent functionality still works correctly