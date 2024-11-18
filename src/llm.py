import numpy as np
import pandas as pd
import torch
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient
import streamlit as st

@st.cache_data()
def load_data():
    dataset = load_dataset("csv", data_files="train.csv")
    data = dataset['train'].to_pandas()
    return data

@staticmethod
@st.cache_data()
def get_embeddings(data):
    not_embedding_columns = ['index', 'title', 'text_chunk', 'new_column']
    # Convert embeddings to tensor
    res = data.drop(columns=not_embedding_columns)
    res = torch.from_numpy(res.to_numpy()).to(torch.float)
    return res

# Load the data
data = load_data()

embeddings = get_embeddings(data)

# Check for NaN values in the embeddings
# nan_indices = ~np.isnan(embeddings.numpy()).any(axis=1)
# if np.any(nan_indices):
#     print("NaN values found in embeddings at indices:", np.where(nan_indices)[0])
# len(embeddings[nan_indices])

# Generating augmented prompts
def augment_prompt(prompt, top_k=10):
    """
    prompt = 'Insects'

    """
    
    from sentence_transformers import SentenceTransformer    
    from sentence_transformers.util import semantic_search
    
    ST = SentenceTransformer('all-MiniLM-L6-v2')
    query_embeddings = ST.encode(prompt)

    # Search the query against the augmented database
    
    hits = semantic_search(
        query_embeddings,
        embeddings,
        top_k=top_k)

    selected_rows = [hits[0][i]['corpus_id'] for i in range(len(hits[0]))]

    # Get context
    context = data.loc[selected_rows]['new_column'].values.tolist()
    context = "\n\n".join([x for x in context])

    documents = data.loc[selected_rows,'title'].values.tolist()
    docs = list(set([x.replace(".pdf", "") for x in documents]))
    docs = "\n".join([f"• {item}" for item in docs])
    
    return context, docs

# import textwrap
# print(textwrap.fill(context,80))
# testing zone
# print(augment_prompt("gorillas", top_k=3)[1])

##################################################################
# Create the chatbot
##################################################################

# hf_key get from secrets

def llm(prompt, context, model='mistral', top_k=3):
    """
    Sample prompt: "Tell me about gorillas at the field museum."
    outputs chatbot response
    """
    
    # if model == 'llama3':
        # client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", api_key="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")
    if model == 'mistral':
        client = InferenceClient("Qwen/Qwen2.5-1.5B", api_key="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")

    # RAG step
    # prompt_aug = augment_prompt(prompt, top_k = top_k)
    # context = prompt_aug[0]

    augmented_prompt = f"""

    Using the following context, answer the question. If you don't know the 
    answer, say that you don't know, don't try to make up an answer. Imagine 
    that you work in a museum  and you are cordially answering visitors' questions.
    Respond by saying hello on behalf of the Field Museum and thanking them for asking.
    Answer the question in English.

    Context: {context}

    Question: {prompt}

    """

    messages = [{"role": "user", "content": augmented_prompt}]
    client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", api_key=hf_key)
    result = client.chat_completion(messages, max_tokens=500, stream=False)
    
    output = result.choices[0].message.content
    
    return output
    # Access different components of the response
    # import textwrap
    # print(textwrap.fill(result.choices[0].message.content, width=70))
    # print(textwrap.fill(context[0]))

# Testing
# aug_prompt = augment_prompt("Tell me about gorillas")
# context = aug_prompt[0]
# documents = aug_prompt[1]
# llm(prompt="Tell me about gorillas", context=context)

