#!/usr/bin/env python3
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import Ollama
import chromadb
import os
import argparse
import time
import streamlit as st

# Streamlit framework
st.title('Private GPT demo')
query = st.text_input("Search the topic you want")
model = os.environ.get("MODEL", "qwen2:0.5b")
# For embeddings model, the example uses a sentence-transformers model
# https://www.sbert.net/docs/pretrained_models.html 
# "The all-mpnet-base-v2 model provides the best quality, while all-MiniLM-L6-v2 is 5 times faster and still offers good quality."
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
persist_directory = os.environ.get("PERSIST_DIRECTORY", "db")
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS', 4))

from constants import CHROMA_SETTINGS

# Function to parse arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='privateGPT: Ask questions to your documents without an internet connection, '
                                                 'using the power of LLMs.')
    parser.add_argument("--hide-source", "-S", action='store_true',
                        help='Use this flag to disable printing of source documents used for answers.')
    parser.add_argument("--mute-stream", "-M",
                        action='store_true',
                        help='Use this flag to disable the streaming StdOut callback for LLMs.')
    return parser.parse_args()

# Main function
def main():
    # Parse the command line arguments
    args = parse_arguments()
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
    # activate/deactivate the streaming StdOut callback for LLMs
    callbacks = [] if args.mute_stream else [StreamingStdOutCallbackHandler()]
    llm = Ollama(model=model, callbacks=callbacks)
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=not args.hide_source)
    
    # Trigger the query when the button is clicked
    if st.button("Submit"):
        if query and query.strip() != "":
            start = time.time()
            res = qa(query)
            answer, docs = res['result'], [] if args.hide_source else res['source_documents']
            end = time.time()
            st.write(answer)
            # if not args.hide_source:
            #     for document in docs:
            #         st.write("> " + document.metadata["source"] + ":")
            #         st.write(document.page_content)

if __name__ == "__main__":
    main()
