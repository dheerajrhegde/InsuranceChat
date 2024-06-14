from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.storage import LocalFileStore
from langchain_community.chat_models import ChatOpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_core.prompts import ChatPromptTemplate
import os
from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import StrOutputParser

index_name = "insuranceplans"
embeddings = OpenAIEmbeddings()
vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)

store = LocalFileStore("./filestore")
# store= InMemoryStore()
id_key = "doc_id"

metadata_field_info = [
    AttributeInfo(
        name="filename",
        description="The file the chunk is from. Is also the plan name",
        type="string",
    ),
]

document_content_description = "Cigna Plan Information"
model = ChatOpenAI(model="gpt-4o")

"""retriever = MultiVectorRetriever(
    metadata_field_info=metadata_field_info,
    vectorstore=vectorstore,
    docstore=store,
    id_key=id_key,
)"""

retriever = SelfQueryRetriever.from_llm(
    llm=model,
    document_contents=document_content_description,
    metadata_field_info=metadata_field_info,
    vectorstore=vectorstore,
    verbose=True
)

# Prompt template
template = """
        If provided, use plan name {plan_name} to answer the question.
        Answer the question based only on the following context, 
        which can include text and tables: {context}
        
        Using the context, follow below steps to answer the question '''{query}'''
        Step 1: Read the retrieved documents' metadata to ensure it is for the plan_name provided. If no plan name is provided, you can ignore this step
        Step 2: Convert any HTML tables provided in the context to strcutured table and understand the column and row labels
        Step 3: Using the text context and understanding of HTML table structure from earlier, answer the question
        Step 4: If the response can be better answered using the table, provide the table in HTML format. And present the text as HTML paragraphs
        """
prompt = ChatPromptTemplate.from_template(template)

# RAG pipeline
chain = RunnableParallel(
    {
        'context': lambda x: retriever.get_relevant_documents(x["query"]),
        'query': lambda x: x["query"],
        'plan_name': lambda x: x["plan_name"]
    }) | prompt | model | StrOutputParser()

print("invoking chain")
response = chain.invoke(
    {
        "query": "What is the coverage for having a baby?",
        "plan_name": "Connect Silver-3 500 Indiv Med Deductible"
    }
)
print(response)

print("invoking chain")
response = chain.invoke(
    {
        "query": "Which plan provides the best coverage for having a baby?",
        "plan_name": ""
    }
)
print(response)