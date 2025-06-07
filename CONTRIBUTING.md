## Development Setup

1. Create a python virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment and install dependencies:
```bash
source ./venv/bin/active
(.venv) pip install -r requirements.txt
```

3. Create a docs folder to store your documents:
```bash
cd <my_repo_clone>
mkdir ./docs/
```

4. Run ollama:
```bash
ollama serve
```

5. Pull required models:
```bash
ollama pull granite3.3:2b
ollama pull nomic-embed-text:latest
```

6. Modify the `config.py` file to change models, system prompt, etc.
```bash
vim ./config.py
```

7. Make your code changes and test them.
```bash
./cta.py -i -s -d ./docs/
```

8. Create a pull request with your changes.

## Commit Guidelines
This project uses conventional commit guidelines: 
<https://www.conventionalcommits.org/en/v1.0.0/>