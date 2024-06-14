from pydantic import BaseModel
from unstructured.partition.pdf import partition_pdf
import unstructured
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.retrievers.multi_vector import MultiVectorRetriever
import os
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document


index_name = "insuranceplans"

# Path to save images
path = "./cigna/"
import os
files = os.listdir("./cigna")
raw_pdf_elements = []
for file in files:
    print("Starting with file", file)
    if file != ".DS_Store":
        raw_pdf_elements = raw_pdf_elements + partition_pdf(
                    filename=path + file,
                    # Using pdf format to find embedded image blocks
                    extract_images_in_pdf=False,
                    # Use layout model (YOLOX) to get bounding boxes (for tables) and find titles
                    # Titles are any sub-section of the document
                    infer_table_structure=True,
                    # Post processing to aggregate text once we have the title
                    chunking_strategy="by_title",
                    # Chunking params to aggregate text blocks
                    # Attempt to create a new chunk 3800 chars
                    # Attempt to keep chunks > 2000 chars
                    # Hard max on chunks
                    max_characters=4000,
                    new_after_n_chars=3800,
                    combine_text_under_n_chars=2000,
                    image_output_dir_path=path,
                )
    print("raw_pdf_elements is now of size", len(raw_pdf_elements))


metadata_field_info = [
    AttributeInfo(
        name="filename",
        description="The file the chunk is from. Is also the plan name",
        type="string",
    ),
]

document_content_description = "Cigna Plan Information"
model = ChatOpenAI(model="gpt-4o")

index_name = "insuranceplans"
embeddings = OpenAIEmbeddings()

vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)

retriever = SelfQueryRetriever.from_llm(
    llm=model,
    document_contents=document_content_description,
    metadata_field_info=metadata_field_info,
    vectorstore=vectorstore,
    verbose=True
)

for e in raw_pdf_elements:
    d = Document(page_content=e.text, metadata=e.metadata.to_dict())
    print(e.id)
    d.metadata = {"filename":d.metadata["filename"]}
    if isinstance(e,unstructured.documents.elements.Table):
        d.page_content = d.page_content + d.metadata.get("text_as_html", " ")
    retriever.vectorstore.add_documents([d])