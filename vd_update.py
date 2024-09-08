import time
import os
import logging
import sys
import atexit
import signal

from watchdog.observers import Observer
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.readers.obsidian import ObsidianReader
from llama_index.readers.file import MarkdownReader

from llama_index.core import load_index_from_storage
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.storage.index_store import SimpleIndexStore

    
# from llama_index.vect


from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

from monitoring import FileChangeTracker, MyHandler

from dotenv import load_dotenv

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

def update_llama_index_settings():
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    model_name = os.environ.get('AZURE_OPENAI_MODEL')
    embed_model_name = 'text-embedding-3-small'
    deployment_name = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME')

    llm = AzureOpenAI(
        model=model_name,
        deployment_name=deployment_name,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
    )

    # You need to deploy your own embedding model as well as your own chat completion model
    embed_model = AzureOpenAIEmbedding(
        model=embed_model_name,
        deployment_name=embed_model_name,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
)

    Settings.llm = llm
    Settings.embed_model = embed_model

# @ this should be a thread
class VectorDatabaseUpdater:
    def __init__(self, obsidian_path, persist_dir):
        self.obsidian_path = obsidian_path
        self.tracker = FileChangeTracker()
        self.index = None
        self.persist_dir = persist_dir
        self._init_index()
        atexit.register(self.save_index)
        self._init_chat_engine()
               
    def _init_index(self):
        
        storage_context = StorageContext.from_defaults(
            docstore=SimpleDocumentStore.from_persist_dir(persist_dir=self.persist_dir),
            vector_store=SimpleVectorStore.from_persist_dir(
                persist_dir=self.persist_dir
            ),
            index_store=SimpleIndexStore.from_persist_dir(persist_dir=self.persist_dir),
        )
        
        self.index = load_index_from_storage(storage_context)
        
    def _init_chat_engine(self):
        self.chat_engine = self.index.as_chat_engine()
        
    def chat(self, prompt):
        streaming_response = self.chat_engine.stream_chat(prompt)
        return "".join(streaming_response.response_gen)

    def watch_directory(self, path, ignore_patterns, interval=5, compute_index=False):
        if compute_index:
            self._compute_vector_store(path)
            
        event_handler = MyHandler(self.tracker, ignore_patterns=ignore_patterns)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(interval)
                self.process_changes()
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        
    def save_index(self, persist_dir = None):
        print("Saving Index")
        persist_dir = persist_dir or self.persist_dir
        self.index.storage_context.persist(persist_dir)
        

    def process_changes(self):
        changes = self.tracker.get_changes()
        for event_type, file_path in changes:
            if event_type == 'created':
                self.add_file(file_path)
            elif event_type == 'modified':
                self.update_file(file_path)
            elif event_type == 'deleted':
                self.delete_file(file_path)
            elif event_type == 'moved':
                self.move_file(file_path[0], file_path[1])
        self.tracker.clear_changes()
        
    # def load_file = 
        
    def read_file(self, file_path):
        document = MarkdownReader().load_data(file_path)
            
        metadata = {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
        }
        
        for chunk in document:
            chunk.metadata = metadata
            chunk.doc_id = file_path
        
        return document

    def add_file(self, file_path):
        print(f"Add file operations {file_path}")
        try:
            document = self.read_file(file_path)
            
            for chunk in document:
                self.index.insert(chunk)
                
        except FileNotFoundError:
            print(f"File not found: {file_path}")

    def update_file(self, file_path):
        print(f"Update file operations{file_path}")
        
        documents = self.read_file(file_path)
        self.index.refresh_ref_docs(documents)

    def delete_file(self, file_path):
        print(f"Delete file operations{file_path}")
        self.index.delete_ref_doc(file_path, delete_from_docstore=True)

    def move_file(self, src_path, dest_path):
        print(f"Move file operations{src_path} -> {dest_path}")
        self.delete_file(src_path)
        self.add_file(dest_path)

    def manual_update(self):
        print("Manual update")
        self.process_changes()
        
        
if __name__ == "__main__":
    ignore_patterns = [".obsidian/*"]
    path = os.path.join("/Users/mo/Library/Mobile Documents/iCloud~md~obsidian/Documents/MainVault/TechNotes")
    persist_dir = "./data/tech_notes"
    uri = "./data/obsidian_lancdb"
    table_name = 'vectors'
    
    update_llama_index_settings()
    
    updater = VectorDatabaseUpdater(obsidian_path=path, persist_dir=persist_dir)
    
    
    updater.watch_directory(path = path, ignore_patterns=ignore_patterns)
    
    