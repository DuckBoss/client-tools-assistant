#!/usr/bin/env python3

import os
import logging
import argparse
import signal
import ollama
import chromadb

import config

from docling.document_converter import DocumentConverter
from docling.exceptions import ConversionError

from rich import print
from rich.console import Console
from rich_argparse import RichHelpFormatter

logger = logging.getLogger("docling_core").setLevel(logging.FATAL)


# set up signal to handle cancelling process
def signal_handler(sig, frame):
    console.print("Ctrl+C pressed. Exiting gracefully...")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)

# set up rich console
console = Console()


def main(args):
    if not args.docs or len(args.docs) == 0:
        console.print("Error: documentation for RAG not found. Please check '--help'.")
        exit(1)
    else:
        config.sources_dir = str(args.docs).strip()

    docs_location: str = None
    try:
        docs_location = os.path.abspath(config.sources_dir)
    except IOError as err:
        console.print(f"Error: documentation path is invalid: {err}")
        exit(1)

    use_one_shot: bool = False
    if not args.interactive:
        if len(args.prompt) == 0 or args.prompt is None:
            console.print(
                "Error: In non-interactive mode, a prompt must be provided. Please check '--help'."
            )
            exit(1)
        use_one_shot = True

    converted_docs = convert_files(docs_location)
    chroma_collection = embed_docs_data(converted_docs)
    if use_one_shot:
        collapsed_prompt = " ".join(args.prompt).strip()
        console.print(f"[bold yellow]Prompt received:[/bold yellow] {collapsed_prompt}")
        one_shot(chroma_collection, user_prompt=collapsed_prompt, stream=args.stream)
    else:
        loop(chroma_collection, stream=args.stream)


# get files converted to text data to embed
def convert_files(docs_location: str) -> list[list[str, str]]:
    docs_converted: list[str] = []
    docs_found: list[str] = []

    with console.status("[bold green]Retrieving documents..."):
        docs_processed: int = 0

        docs_location = os.path.abspath(docs_location)
        for doc in os.listdir(docs_location):
            doc_path: str = os.path.abspath(os.path.join(docs_location, doc))
            # console.print(doc_path)
            if os.path.isdir(doc_path):
                continue  # Don't scan sub-directories
            if (
                not doc_path.endswith("pdf")
                and not doc_path.endswith("docx")
                and not doc_path.endswith("html")
                and not doc_path.endswith("xlsx")
            ):
                continue  # Don't scan incompatible files
            docs_found.append(doc_path)
        if not len(docs_found) > 0:
            console.print(
                "Error: no documents found. Please add documents to your docs folder. Please check '--help'."
            )
            exit(1)
    console.print(
        f"[bold yellow]{len(docs_found)}[/bold yellow] documents retrieved for processing."
    )

    with console.status("[bold green]Preparing documents into compatible format..."):
        converter = DocumentConverter()
        for doc in docs_found:
            doc_name = os.fsdecode(doc)
            try:
                doc_cv = converter.convert(doc).document
            except ConversionError as err:
                console.print(
                    f"Error: cannot convert document, skipping: {doc_name} : {err}"
                )
                continue
            except ValueError as err:
                console.print(
                    f"Error: invalid document contents, skipping: {doc_name} : {err}"
                )
                continue
            text = doc_cv.export_to_text()
            docs_converted.append(text)
            console.print(
                f"[bold yellow][{docs_processed + 1}/{len(docs_found)}][/bold yellow] Document [bold magenta]{os.path.basename(doc_name)}[/bold magenta] prepared."
            )
            docs_processed += 1
    if len(docs_converted) == 0:
        console.print(
            "Error: no documents were converted. Check that the files are valid."
        )
        exit(1)
    return docs_converted


def embed_docs_data(converted_docs):
    # store each document in a vector embedding database
    client = chromadb.Client()
    collection = client.create_collection(name="docs")
    with console.status("[bold green]Generating vector embedding database..."):
        for idx, doc in enumerate(converted_docs):
            response = ollama.embed(model=config.embed_model, input=doc)
            embeddings = response["embeddings"]
            collection.add(
                ids=[str(idx)],
                embeddings=embeddings,
                documents=[doc],
            )
    console.print("Documents embeddings generated.")
    return collection


def one_shot(chroma_collection, user_prompt, stream=False):
    # generate batch embeddings for the input and
    # retrieve the most relevant document
    data = None
    with console.status("[bold green]Creating prompt embeddings..."):
        response = ollama.embed(model=config.embed_model, input=user_prompt)
        results = chroma_collection.query(
            query_embeddings=response["embeddings"], n_results=1
        )
        data = results["documents"][0][0]
        # console.print("Prompt embeddings generated.")

    # generate a response combining the prompt and data
    print("\n")
    if stream:
        for chunk in ollama.generate(
            model=config.llm_model,
            system=config.system_prompt,
            prompt=f"Using this data: {data}. Respond to this prompt: {user_prompt}",
            stream=True,
        ):
            console.print(chunk["response"], end="")
    else:
        with console.status("[bold green]Creating prompt embeddings..."):
            resp = ollama.generate(
                model=config.llm_model,
                system=config.system_prompt,
                prompt=f"Using this data: {data}. "
                f"Respond to this prompt: {user_prompt}",
                stream=False,
            )
            console.print(resp["response"])
    print("\n")


def loop(chroma_collection, stream=False):
    while True:
        user_prompt = console.input(
            prompt="\n[bold magenta]Ask a question to the "
            "Client Tools AI Assistant:[/bold magenta]\n> "
        ).strip()
        if user_prompt.lower() == "exit":
            console.print("Exiting...")
            exit(0)
        elif len(user_prompt) == 0 or user_prompt.lower() == "help":
            console.print("Type 'exit' to exit, or ask a question to the AI.")
            continue

        # generate batch embeddings for the input and
        # retrieve the most relevant document
        data = None
        with console.status("[bold green]Creating embeddings..."):
            response = ollama.embed(model=config.embed_model, input=user_prompt)
            results = chroma_collection.query(
                query_embeddings=response["embeddings"], n_results=1
            )
            data = results["documents"][0][0]
            # console.print("Prompt embeddings generated.")

        # generate a response combining the prompt and data
        print("\n")
        if stream:
            for chunk in ollama.generate(
                model=config.llm_model,
                system=config.system_prompt,
                prompt=f"Using this data: {data}. "
                f"Respond to this prompt: {user_prompt}",
                stream=True,
            ):
                console.print(chunk["response"], end="")
        else:
            with console.status("[bold green]Creating embeddings..."):
                resp = ollama.generate(
                    model=config.llm_model,
                    system=config.system_prompt,
                    prompt=f"Using this data: {data}. "
                    f"Respond to this prompt: {user_prompt}",
                    stream=False,
                )
                console.print(resp["response"])
        print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Client Tools Assistant (CTA)",
        description="A local RAG-based AI assistant to retrieve team workflows and processes information from locally stored documents",
        formatter_class=RichHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--stream",
        action="store_true",
        help="enable streaming generated responses",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="enable interactive prompting",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-d",
        "--docs",
        help="path to local directory of documents to use for rag prompting",
        required=False,
        default="./docs/",
    )
    parser.add_argument(
        "prompt", nargs="*", help="prompt for the AI assistant", default=""
    )
    args = parser.parse_args()

    main(args)
