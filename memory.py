from langchain_chroma import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_core.documents import Document
import os

# Retrieve the API key from the environment


class MemoryDatabase:
    def __init__(self, collection_name="sample_collection", persist_directory="./memory_databases"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large",openai_api_key=self.api_key )  # Initialize embeddings
        self.vector_store = Chroma(collection_name=collection_name, persist_directory=persist_directory, embedding_function=self.embeddings)

    def _format_memory_content(self, task, plan, observation):
        """
        Formats the task, plan, and observation into a single string.
        """
        content = (
            f"Task: {task}\n"
            f"Blueprint: {plan}\n"
            # f"Observation: {observation}"
        )
        return content

    def store_plan(self, task, observation, plan):
        """
        Stores the formatted memory in the vector store.
        """
        # Format the memory content
        content = self._format_memory_content(task, plan, observation)

        # Create a document with the formatted content
        document = Document(page_content=content)

        # Add the document to the vector store
        self.vector_store.add_documents([document])


    def save_index(self):
        """
        Persists the vector store to disk.
        """
        self.vector_store.persist()

    def retrieve_similar(self, query, k=3):
        """
        Retrieves documents similar to the query from the vector store.
        """
        results = self.vector_store.similarity_search_with_score(query, k=3)
        for res, score in results:
            print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")


    def delete(self):
        idsList = self.vector_store.get()['ids']
        self.vector_store._collection.delete(ids=idsList)

    def manage_memories(self):
        """
        Displays each memory instance and prompts the user to delete it based on input.
        """
        # Retrieve all documents and their IDs
        data = self.vector_store.get()
        documents = data.get('documents', [])
        ids = data.get('ids', [])

        if not documents:
            print("No memories found to manage.")
            return

        print(f"Found {len(documents)} memory/memories.\n")

        for doc, doc_id in zip(documents, ids):
            print(f"ID: {doc_id}")
            print("Content:")
            print(doc)
            print("-" * 40)

            while True:
                choice = input("Do you want to delete this memory? (yes/no): ").strip().lower()
                if choice in ['yes', 'y']:
                    self.vector_store._collection.delete(ids=[doc_id])
                    print("Memory deleted.\n")
                    break
                elif choice in ['no', 'n']:
                    print("Memory retained.\n")
                    break
                else:
                    print("Invalid input. Please enter 'yes' or 'no'.\n")

        print("Memory management complete.\n")