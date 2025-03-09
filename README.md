# Discussion-Llama

A multi-role discussion system that simulates conversations between different roles on a given topic, with the goal of reaching consensus.

## Overview

Discussion-Llama is a system that allows you to simulate discussions between different roles (e.g., Product Owner, Backend Developer, UI/UX Designer) on a given topic. The system uses language models to generate responses for each role, and aims to reach consensus on the topic.

## Features

- Define roles with specific attributes and behaviors using YAML files
- Simulate discussions between different roles on a given topic
- Automatically detect consensus among participants
- Memory-efficient implementation with disk-based state management
- Support for different LLM backends (currently Ollama and a mock implementation)
- Command-line interface for running discussions

## Installation

### Prerequisites

- Python 3.7 or higher
- [Ollama](https://ollama.ai/) (optional, for using real language models)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/discussion-llama.git
cd discussion-llama

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Running the Program

There are two main ways to run Discussion-Llama:

### 1. Using the run_discussion.py script

```bash
# Basic usage
python run_discussion.py "How should we implement user authentication in our app?"

# Specify roles to include
python run_discussion.py "How should we implement user authentication in our app?" --roles "product_owner_pm,backend_developer,security_engineer"

# Use Ollama for LLM integration
python run_discussion.py "How should we implement user authentication in our app?" --llm-client ollama --model llama2:7b-chat-q4_0

# Use enhanced Ollama client with streaming
python run_discussion.py "How should we implement user authentication in our app?" --llm-client enhanced_ollama --model llama2:7b-chat-q4_0 --stream

# Save results to a file
python run_discussion.py "How should we implement user authentication in our app?" --output results.json
```

### 2. Using the installed command-line interface

If you've installed the package with `pip install -e .`, you can use the `discussion-llama` command:

```bash
# Basic usage
discussion-llama "How should we implement user authentication in our app?"

# With additional options
discussion-llama "How should we implement user authentication in our app?" --roles "product_owner_pm,backend_developer,security_engineer" --llm-client ollama
```

## Command-line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--roles` | Comma-separated list of role names to include | Auto-selected based on topic |
| `--num-roles` | Number of roles to include (if not specified) | 3 |
| `--max-turns` | Maximum number of turns | 10 |
| `--llm-client` | LLM client to use (mock, ollama, enhanced_ollama) | mock |
| `--model` | Model to use (for Ollama) | llama2:7b-chat-q4_0 |
| `--max-retries` | Maximum number of retries for LLM requests | 3 |
| `--retry-delay` | Delay between retries for LLM requests | 1.0 |
| `--timeout` | Timeout for LLM requests in seconds | 30 |
| `--output` | Output file for discussion results (JSON) | None |
| `--stream` | Use streaming for response generation (enhanced_ollama only) | False |

## Using with Ollama

To use Discussion-Llama with real language models, you need to install and run Ollama:

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Start the Ollama server
3. Pull the model you want to use:
   ```bash
   ollama pull llama2:7b-chat-q4_0
   ```
4. Run Discussion-Llama with the Ollama client:
   ```bash
   python run_discussion.py "Your topic" --llm-client ollama --model llama2:7b-chat-q4_0
   ```

## Python API

You can also use Discussion-Llama programmatically:

```python
from discussion_llama.role import load_roles_from_yaml
from discussion_llama.engine import DiscussionEngine
from discussion_llama.llm import create_llm_client

# Load roles
roles = load_roles_from_yaml("./roles")

# Create LLM client
llm_client = create_llm_client("ollama", model="llama2:7b-chat-q4_0")

# Create and run discussion engine
engine = DiscussionEngine("How should we implement user authentication in our app?", roles)
result = engine.run_discussion()

# Print results
for message in result["discussion"]:
    print(f"[{message['role']}]: {message['content']}")
```

## Role Definitions

Roles are defined in YAML files in the `roles` directory. Each role has the following attributes:

- `role`: The name of the role
- `description`: A description of the role
- `responsibilities`: A list of responsibilities for the role
- `expertise`: A list of areas of expertise for the role
- `characteristics`: A list of characteristics for the role
- `interaction_with`: A dictionary of roles that this role interacts with
- `success_criteria`: A list of success criteria for the role

## License

This project is licensed under the MIT License - see the LICENSE file for details.