# E2B Template Build Guide

This guide explains how to build and deploy the custom E2B template for async-code agents.

## Prerequisites

1. **E2B Account**: Sign up at [e2b.dev](https://e2b.dev)
2. **E2B CLI**: Install globally
   ```bash
   npm install -g @e2b/cli
   ```
3. **Authentication**: Login to E2B
   ```bash
   e2b auth login
   ```

## Building the Template

1. **Navigate to template directory**:
   ```bash
   cd server-e2b/e2b-template
   ```

2. **Build the template**:
   ```bash
   e2b template build
   ```
   
   This will:
   - Build the Docker image locally
   - Upload it to E2B's registry
   - Return a template ID (e.g., `async-code-agents-abc123`)

3. **Verify the template**:
   ```bash
   e2b template list
   ```
   
   You should see your template in the list.

## Deploying to Production

1. **Update environment variables**:
   
   Add to your `.env` file:
   ```bash
   E2B_TEMPLATE_ID=async-code-agents-abc123  # Use your actual template ID
   ```

2. **Test the template**:
   ```bash
   # From server-e2b directory
   python test_e2b_integration.py
   ```

3. **Deploy your application**:
   
   The application will automatically use the custom template when `E2B_TEMPLATE_ID` is set.

## What's Pre-installed

The custom template includes:

- **System packages**:
  - git
  - curl
  - python3 (3.11)
  - nodejs (18.x)
  - npm

- **Python packages**:
  - openai
  - anthropic
  - requests

- **Node packages**:
  - @anthropic-ai/claude-cli (global)

## Benefits

Using this custom template provides:

1. **Faster startup**: No need to install dependencies per task (saves 30-60s)
2. **Lower costs**: Less compute time spent on installations
3. **Better reliability**: Pre-tested dependency versions
4. **Consistent environment**: All tasks run in identical setups

## Updating the Template

If you need to add new dependencies:

1. Edit `Dockerfile`
2. Increment a version comment in the Dockerfile
3. Run `e2b template build` again
4. Update `E2B_TEMPLATE_ID` in your environment

## Troubleshooting

### Build Failures

If the build fails:
- Check Docker is running locally
- Ensure you're authenticated: `e2b auth status`
- Check E2B service status

### Template Not Found

If the app can't find your template:
- Verify `E2B_TEMPLATE_ID` is set correctly
- Check template exists: `e2b template list`
- Ensure your E2B API key has access to the template

### Performance Issues

If tasks still seem slow:
- Check logs to confirm template is being used
- Verify dependencies aren't being reinstalled
- Monitor E2B dashboard for sandbox startup times

## Cost Optimization

Custom templates may have different pricing:
- Check E2B pricing for custom template storage
- Monitor usage in E2B dashboard
- Consider template size (smaller = faster startup)

## CI/CD Integration

For automated deployments:

```yaml
# GitHub Actions example
- name: Build E2B Template
  run: |
    npm install -g @e2b/cli
    e2b auth login --api-key ${{ secrets.E2B_API_KEY }}
    cd server-e2b/e2b-template
    TEMPLATE_ID=$(e2b template build --json | jq -r .id)
    echo "E2B_TEMPLATE_ID=$TEMPLATE_ID" >> $GITHUB_ENV
```

## Monitoring

Monitor template usage:
- E2B dashboard shows template usage stats
- Application logs show template ID when creating sandboxes
- Track task startup times before/after template