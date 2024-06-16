# Set the default shell
set shell := ["bash", "-cu"]

# Set the Python interpreter
PYTHON := "python3.11"

# Set the default file path
FILE_PATH := "~/Downloads"

# Set the OpenAI API key
OPENAI_API_KEY := env_var_or_default('OPENAI_API_KEY', '')

# Setup the repository
setup:
    #!/usr/bin/env bash
    set -euxo pipefail
    
    # Install libmagic using Homebrew
    brew install libmagic

    # Install UV using Homebrew
    brew install uv

    # Create a virtual environment
    {{PYTHON}} -m venv .venv

    # Activate the virtual environment
    source .venv/bin/activate

    # Compile the requirements
    uv pip compile pyproject.toml -o requirements.txt

    # Install the dependencies
    uv pip sync requirements.txt

    # Install the python-dotenv package
    pip install python-dotenv

# Run the application
run: setup
    #!/usr/bin/env bash
    set -euxo pipefail

    # Activate the virtual environment
    source .venv/bin/activate
    source .env

    # Run the application with the specified file path
    python -m app demo "{{FILE_PATH}}" --producer openai 

# Set the file path
set-file-path FILE_PATH:
    #!/usr/bin/env bash
    set -euxo pipefail

    # Update the file path
    FILE_PATH="{{FILE_PATH}}"
    echo "File path set to: {{FILE_PATH}}"

# Set the OpenAI API key
set-openai-key OPENAI_API_KEY:
    #!/usr/bin/env bash
    set -euxo pipefail

    # Update the OpenAI API key
    echo "export OPENAI_API_KEY={{OPENAI_API_KEY}}" > .env
    echo "OpenAI API key set and written to .env file"