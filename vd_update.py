import time
import os
import logging
import sys

import lancedb
from watchdog.observers import Observer
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from llama_index.readers.obsidian import ObsidianReader
from llama_index.readers.file import MarkdownReader
# from llama_index.vect


from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

from monitoring import FileChangeTracker, MyHandler

from dotenv import load_dotenv

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

load_dotenv()

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
    def __init__(self, obsidian_path, uri, table_name="vectors"):
        self.obsidian_path = obsidian_path
        self.uri = uri
        self.table_name = table_name
        self.tracker = FileChangeTracker()
        self.vector_store = None
        self.index = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        #TODO: update this - load from LanceDB persistent storage
        self._init_db_table(self.uri, self.table_name)
        
        if hasattr(self, 'lance_table') and self._init_db_table is not None:
            self._index_from_lancedb(self.lance_table)
        
    def _init_db_table(self, path, table_name):
        try:
            self.db = lancedb.connect(uri=path)
            self.lance_table = self.db.open_table(table_name)
        except Exception as e:
            print(e)
        
    def _index_from_lancedb(self, table):
        self.vector_store = LanceDBVectorStore.from_table(table)
        self.index = VectorStoreIndex.from_vector_store(self.vector_store)
    
    
    def _compute_vector_store(self, path):
        obsidian_documents = ObsidianReader(input_dir=self.path).load_data()
        self.vector_store = LanceDBVectorStore(
            uri=self.uri, mode="overwrite", query_type="hybrid"
        )
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex.from_documents(
            obsidian_documents, storage_context=storage_context
        )

    def watch_directory(self, path, ignore_patterns, interval=10, compute_index=False):
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

    def add_file(self, file_path):
        print(f"Add file operations {file_path}")
        document = MarkdownReader().load_data(file_path)
        
        self.index.insert(document[0])

    def update_file(self, file_path):
        print(f"Update file operations{file_path}")
        # Option 1: Update existing file
        self.delete_file(file_path)
        self.add_file(file_path)

    def delete_file(self, file_path):
        print(f"Delete file operations{file_path}")
        # Assuming the vector store has a method to delete by document ID or file path
        self.vector_store.delete(file_path)

    def move_file(self, src_path, dest_path):
        print(f"Move file operations{src_path} -> {dest_path}")
        self.delete_file(src_path)
        self.add_file(dest_path)

    def manual_update(self):
        print("Manual update")
        self.process_changes()
        
        
if __name__ == "__main__":
    ignore_patterns = [".obsidian/*"]
    path = os.path.join("/Users/mo/Library/Mobile Documents/iCloud~md~obsidian/Documents/MainVault")
    
    uri = "./data/obsidian_lancdb"
    table_name = 'vectors'
    
    update_llama_index_settings()
    
    updater = VectorDatabaseUpdater(obsidian_path=path, uri=uri, table_name=table_name)
    
    
    updater.watch_directory(path = path, ignore_patterns=ignore_patterns)
    
    