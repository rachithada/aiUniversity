from rag.rag_pipeline import retrieve_docs
query = "What is attendance policy?"
context = retrieve_docs(query)
print(context)