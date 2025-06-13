# Agent Scripts

This directory contains sophisticated agent scripts that are uploaded to E2B sandboxes for execution.

## Overview

Instead of generating agent code inline, we maintain reusable scripts here that can:
- Be tested independently
- Handle complex scenarios
- Provide better error handling
- Be versioned and improved over time

## Scripts

### codex_agent.py

A sophisticated GPT/Codex agent that:
- Analyzes repository structure for context
- Generates appropriate system prompts
- Handles API errors gracefully
- Supports configuration via environment variables
- Reads prompts from files (avoiding injection issues)

## Usage

The scripts are automatically uploaded to E2B sandboxes when needed. The main code in `code_task_e2b_real.py` reads these scripts and uploads them to the sandbox filesystem before execution.

## Adding New Agents

To add a new agent:

1. Create a new Python script in this directory
2. Follow the pattern of reading configuration from environment variables
3. Read the task prompt from `/tmp/agent_prompt.txt`
4. Output results to stdout
5. Update the corresponding method in `code_task_e2b_real.py`

## Environment Variables

Agents should read configuration from environment variables:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GPT_MODEL` - Model to use (default: gpt-4)
- `MAX_TOKENS` - Maximum tokens for response
- `TEMPERATURE` - Temperature for generation

## Security

- Always read prompts from files, never from command line arguments
- Validate all inputs
- Handle errors gracefully
- Don't expose sensitive information in error messages