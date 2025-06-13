# E2B Custom Template for Async-Code Agents

This directory contains the custom E2B sandbox template that pre-installs all dependencies required for AI agent execution.

## Why Custom Template?

Without a custom template, every task execution would need to:
- Install Node.js packages (`npm install -g @anthropic-ai/claude-cli`)
- Install Python packages (`pip install openai`)

This adds 30-60 seconds of overhead per task and increases costs.

## Pre-installed Dependencies

The custom template includes:
- Git
- Node.js 18 & npm
- Python 3.11 & pip
- Claude CLI (`@anthropic-ai/claude-cli`)
- OpenAI Python SDK
- Anthropic Python SDK

## Building the Template

1. Ensure you have E2B CLI installed:
   ```bash
   npm install -g @e2b/cli
   ```

2. Authenticate with E2B:
   ```bash
   e2b auth login
   ```

3. Build the template:
   ```bash
   ./build-template.sh
   ```

4. The script will output a template ID like `async-code-agents-xxxxx`

## Using the Template

Update `server-e2b/utils/code_task_e2b_real.py` to use the custom template:

```python
# Add at the top of the file
E2B_TEMPLATE_ID = os.getenv('E2B_TEMPLATE_ID', 'async-code-agents-xxxxx')

# In the execute_task method
sandbox = await Sandbox.create(
    template=E2B_TEMPLATE_ID,  # Add this line
    api_key=self.api_key,
    env_vars={...},
    timeout=self.SANDBOX_TIMEOUT
)
```

## Environment Variable

Add to your `.env`:
```
E2B_TEMPLATE_ID=async-code-agents-xxxxx
```

## Updating the Template

If you need to add new dependencies:

1. Edit `Dockerfile`
2. Run `./build-template.sh`
3. Update `E2B_TEMPLATE_ID` in your `.env`