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

```bash
# Clone the repository
git clone https://github.com/yourusername/discussion-llama.git
cd discussion-llama

# Install the package
pip install -e .
```

## Usage

### Command-line Interface

```bash
# Run a discussion with default settings
discussion-llama "How should we implement user authentication in our app?"

# Specify roles to include
discussion-llama "How should we implement user authentication in our app?" --roles "product_owner_pm,backend_developer,security_engineer"

# Use Ollama for LLM integration
discussion-llama "How should we implement user authentication in our app?" --llm-client ollama --model llama2:7b-chat-q4_0

# Save results to a file
discussion-llama "How should we implement user authentication in our app?" --output results.json
```

### Python API

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