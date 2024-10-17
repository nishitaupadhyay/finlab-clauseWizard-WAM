import os
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# Step 1: Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Step 2: Specify your file paths and collection name
data_directory = "./data"  # Directory containing the JSON files
json_files = ["funds.json", "clients.json"]  # List of JSON files to process
collection_name = "financial-client-data"  # Name of the ChromaDB collection
persist_directory = "./chromadb/financial-client-data"

print(f"Processing files: {json_files} from directory: {data_directory}")
print(f"Collection name: {collection_name}")

# Step 3: Load and process JSON files
def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

all_documents = []

for file_name in json_files:
    file_path = os.path.join(data_directory, file_name)
    print(f"Loading file: {file_path}")
    
    data = load_json_file(file_path)
    
    if file_name == "clients.json":
        for city, clients in data.items():
            for client in clients:
                all_documents.append(Document(
                    page_content=json.dumps(client),
                    metadata={"type": "client", "city": city}
                ))
    elif file_name == "funds.json":
        all_documents.append(Document(
            page_content=json.dumps(data["default_fund"]),
            metadata={"type": "fund", "fund_type": "default"}
        ))
        for fund in data["funds"]:
            all_documents.append(Document(
                page_content=json.dumps(fund),
                metadata={"type": "fund", "fund_type": "regular"}
            ))

print(f"Total documents loaded: {len(all_documents)}")

# Step 4: Set up OpenAI Embeddings
print("Setting up OpenAI Embeddings...")
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)
print("OpenAI Embeddings set up complete.")

# Step 5: Create a LangChain Chroma vectorstore
print("Creating LangChain Chroma vectorstore...")
db = Chroma.from_documents(
    documents=all_documents,
    embedding=embeddings,
    persist_directory=persist_directory,
    collection_name=collection_name
)
print("Documents added to Chroma vectorstore.")

# Step 6: Verify by retrieving stored documents
print("Retrieving stored documents from Chroma...")
stored_documents = db.get()
print(f"Retrieved {len(stored_documents['documents'])} documents from Chroma.")

# Print a sample of stored documents
print("\nSample of stored documents:")
for idx, (content, meta) in enumerate(zip(stored_documents["documents"][:5], stored_documents["metadatas"][:5])):
    print(f"Document {idx + 1}:")
    print(f"Content: {content[:100]}...")  # Print first 100 characters of content
    print(f"Metadata: {meta}")
    print("-" * 50)

if len(stored_documents['documents']) > 5:
    print(f"... and {len(stored_documents['documents']) - 5} more documents")

print("\nAll documents have been successfully added to Chroma vectorstore.")