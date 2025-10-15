import os
import pandas as pd
import json
import sqlite3
from typing import Dict, List, Any
from loguru import logger
from config import config
import chromadb
from sentence_transformers import SentenceTransformer
import hashlib

class KnowledgeBaseManager:
    def __init__(self):
        self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.chroma_client = chromadb.PersistentClient(path=config.DATA_DIR)
        self.collection = self._get_or_create_collection()
        
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection"""
        try:
            return self.chroma_client.get_collection("knowledge_base")
        except:
            return self.chroma_client.create_collection(
                name="knowledge_base",
                metadata={"description": "Russian Knowledge Base"}
            )
    
    def _generate_document_id(self, content: str) -> str:
        """Generate unique document ID"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - chunk_overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
                
        return chunks
    
    def process_uploaded_file(self, file_path: str) -> Dict[str, Any]:
        """Process uploaded file and add to knowledge base"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            documents = []
            
            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents = self._chunk_text(content)
                
            elif file_ext == '.csv':
                df = pd.read_csv(file_path)
                # Convert all columns to text
                text_content = ""
                for _, row in df.iterrows():
                    text_content += " ".join(str(cell) for cell in row) + "\n"
                documents = self._chunk_text(text_content)
                
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Flatten JSON to text
                text_content = json.dumps(data, ensure_ascii=False)
                documents = self._chunk_text(text_content)
            
            # Add documents to ChromaDB
            if documents:
                self._add_documents_to_kb(documents, os.path.basename(file_path))
                
                return {
                    "success": True,
                    "documents_processed": len(documents),
                    "chunks_created": len(documents)
                }
            else:
                return {"success": False, "error": "No documents extracted"}
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _add_documents_to_kb(self, documents: List[str], source: str):
        """Add documents to knowledge base with embeddings"""
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Prepare documents for ChromaDB
            ids = [self._generate_document_id(f"{source}_{i}") for i in range(len(documents))]
            metadatas = [{"source": source, "chunk_index": i} for i in range(len(documents))]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents from {source} to knowledge base")
            
        except Exception as e:
            logger.error(f"Error adding documents to KB: {e}")
            raise
    
    def semantic_search(self, query: str, top_k: int = config.TOP_K_RESULTS) -> List[Dict]:
        """Perform semantic search on knowledge base"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'content': doc,
                        'similarity': results['distances'][0][i] if results['distances'] else 0,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def reset_knowledge_base(self) -> bool:
        """Reset the knowledge base"""
        try:
            self.chroma_client.delete_collection("knowledge_base")
            self.collection = self.chroma_client.create_collection("knowledge_base")
            
            # Clear knowledge base directory
            for file in os.listdir(config.KNOWLEDGE_BASE_DIR):
                file_path = os.path.join(config.KNOWLEDGE_BASE_DIR, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            logger.info("Knowledge base reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting knowledge base: {e}")
            return False
    
    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """Get information about the knowledge base"""
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "chunk_count": count,  # In this implementation, each chunk is a document
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except:
            return {
                "document_count": 0,
                "chunk_count": 0,
                "last_update": "Never"
            }
