
## Prerequisites

Before getting started, ensure that you have the following prerequisites installed on your Apple Silicon device:

- [Homebrew](https://brew.sh/)
- [Python 3.11](https://www.python.org/downloads/)
- [Just](https://github.com/casey/just)
- [UV] (https://formulae.brew.sh/formula/uv)

## Setup

1. Clone the not-llama-fs repository:
   ```
   git clone https://github.com/ahmedtwine/not-llama-fs.git
   cd not-llama-fs
   ```

2. The `justfile` should already be present in the project directory.

## Usage

1. Set your OpenAI API key:
   ```
   just set-openai-key <your_openai_api_key>
   ```
   Replace `<your_openai_api_key>` with your actual OpenAI API key.

2. (Optional) Set a different file path for running the application:
   ```
   just set-file-path <your_file_path>
   ```
   Replace `<your_file_path>` with the desired file path.

3. Run the application:
   ```
   just run
   ```
   This command will set up the environment and run the application with the specified file path and OpenAI API key.

## Credits
https://github.com/drforse/not-llama-fs