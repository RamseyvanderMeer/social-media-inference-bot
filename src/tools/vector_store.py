"""Initialize ChromaDB and populate with embeddings using LlamaIndex."""

import logging
from pathlib import Path
from typing import List, Optional

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb
from chromadb.config import Settings

from src.config.settings import get_settings
from src.data.loader import DataLoader

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store manager using ChromaDB and LlamaIndex."""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        db_path: Optional[Path] = None,
        force_recreate: bool = False,
    ):
        """Initialize vector store."""
        settings = get_settings()
        self.collection_name = collection_name or settings.vector_store.collection_name
        self.db_path = db_path or settings.vector_store.db_path
        self.force_recreate = force_recreate

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False),
        )

        # Initialize embedding model
        self.embed_model = OpenAIEmbedding(
            model=settings.vector_store.embedding_model
        )

        # Initialize or get collection
        if force_recreate:
            try:
                self.chroma_client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except Exception:
                pass

        try:
            self.chroma_collection = self.chroma_client.get_collection(
                self.collection_name
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            self.chroma_collection = self.chroma_client.create_collection(
                self.collection_name
            )
            logger.info(f"Created new collection: {self.collection_name}")

        # Initialize LlamaIndex vector store
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        self.index: Optional[VectorStoreIndex] = None

    def _chunk_documents(
        self, documents: List[str], chunk_size: int = 512, chunk_overlap: int = 50
    ) -> List[Document]:
        """Chunk documents for indexing."""
        from llama_index.core.node_parser import SimpleNodeParser

        # Create Document objects
        llama_docs = [
            Document(text=doc, metadata={"index": i}) for i, doc in enumerate(documents)
        ]

        # Parse into nodes with chunking
        parser = SimpleNodeParser.from_defaults(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        nodes = parser.get_nodes_from_documents(llama_docs)

        logger.info(
            f"Chunked {len(documents)} documents into {len(nodes)} nodes "
            f"(chunk_size={chunk_size}, overlap={chunk_overlap})"
        )

        return nodes

    def index_documents(
        self,
        documents: List[str],
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> None:
        """Index documents into vector store."""
        logger.info(f"Indexing {len(documents)} documents...")

        # Chunk documents
        nodes = self._chunk_documents(documents, chunk_size, chunk_overlap)

        # Create or update index
        if self.index is None:
            self.index = VectorStoreIndex(
                nodes=nodes,
                storage_context=self.storage_context,
                embed_model=self.embed_model,
            )
        else:
            # Add to existing index
            for node in nodes:
                self.index.insert(node)

        logger.info(f"Indexed {len(nodes)} nodes into vector store")

    def load_index(self) -> VectorStoreIndex:
        """Load existing index from vector store."""
        if self.index is None:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model,
            )
            logger.info("Loaded existing index from vector store")
        return self.index

    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
    ) -> List[dict]:
        """
        Search vector store for similar documents.

        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of search results with text and metadata
        """
        if self.index is None:
            self.load_index()

        retriever = self.index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)

        results = []
        for node in nodes:
            score = node.score if hasattr(node, "score") else 1.0
            if score >= similarity_threshold:
                results.append(
                    {
                        "text": node.text,
                        "metadata": node.metadata,
                        "score": score,
                    }
                )

        logger.info(f"Search returned {len(results)} results for query: {query[:50]}...")
        return results

    def get_collection_size(self) -> int:
        """Get number of documents in collection."""
        return self.chroma_collection.count()


def setup_vector_store(
    data_path: Path = Path("data/mock_x_data.json"),
    force_recreate: bool = False,
) -> VectorStore:
    """Set up and populate vector store with X data."""
    logger.info("Setting up vector store...")

    # Load data
    loader = DataLoader(data_path)
    documents = loader.get_all_documents()

    if not documents:
        raise ValueError(f"No documents found in {data_path}")

    # Create and populate vector store
    vector_store = VectorStore(force_recreate=force_recreate)
    vector_store.index_documents(documents)

    logger.info(
        f"Vector store setup complete. Collection size: {vector_store.get_collection_size()}"
    )

    return vector_store
