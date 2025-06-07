# References Used

## Online tutorials and references

- short tutorial on ollama embedding:
    <https://ollama.com/blog/embedding-models>
- ollama streamed text generation example:
    <https://github.com/ollama/ollama-python/blob/main/examples/generate-stream.py>
- ollama local hosting environment variable fixes:
    <https://github.com/ollama/ollama/issues/2203>

## Documentation Used

- rich cli official docs:
    <https://rich.readthedocs.io/en/latest/>
- docling official docs:
    <https://docling-project.github.io/docling/examples/minimal/>
    <https://github.com/docling-project/docling>
- rh developer generative AI tips for developers:
    <https://developers.redhat.com/articles/2024/10/08/ai-llm-prompt-patterns-developers#>

## Inspirations

- **Ramalama**: I tried implementing this with a simpler solution using ramalama. However, the new RAG features are still in development and not functional.
- **NotebookLM**: I think this is a much more refined solution, but having the ability to interface through the command-line,
or in my ideal scenario through a slack bot, would provide a more natural in-house method of interfacing with this.
- **Command Line Assistant (cla)**: This project inspired me to first work on a cli implementation of this idea and gave me some practical examples of how interfacing with an LLM through a cli would work.
- **Laziness**: Sometimes I just don't want to dig through confluence pages to find what I want. The organization feels lacking right now, and I'd much rather ask a question via slack or CLI to get a quick response. Although this wouldn't work due to possible hallucinating for anything critical, this would be useful to get reminders on small things I may have forgotten from overall workflows and team documentation.
