"""RAG tools for searching and retrieving information from documents."""

import os
from typing import Any

from dotenv import load_dotenv
from langchain_core.tools import tool
from pinecone import Pinecone

# Load environment variables
load_dotenv()


@tool
def search_documents(query: str) -> dict[str, Any]:
    """Search for information in the capstone documents using semantic similarity."""
    print(f"🔍 Searching documents for: {query}")

    try:
        # Initialize Pinecone connection
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(os.getenv("PINECONE_DENSE_INDEX_NAME"))

        # Generate query embedding using Pinecone's built-in embedding
        query_response = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[query],
            parameters={"input_type": "query", "truncate": "END"},
        )
        query_embedding = query_response.data[0].values

        # Search in Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True,
            namespace="default",
        )

        if not results.matches:
            return {
                "message": f"No documents found matching your query: '{query}'",
                "query": query,
                "results": [],
                "suggestion": "Try rephrasing your query or ask about general topics.",
            }

        # Format results
        formatted_results = []
        for match in results.matches:
            text = match.metadata.get("text", "")
            formatted_results.append(
                {
                    "relevance_score": round(match.score, 3),
                    "content": text[:500] + "..." if len(text) > 500 else text,
                    "source": match.metadata.get("source", "Unknown"),
                    "chunk_id": match.id,
                }
            )

        print(f"✅ Found {len(results.matches)} relevant document chunks")

        return {
            "query": query,
            "total_results": len(results.matches),
            "results": formatted_results,
            "search_method": "semantic_similarity",
            "index_name": os.getenv("PINECONE_DENSE_INDEX_NAME"),
        }

    except Exception as e:
        print(f"❌ Document search failed: {e}")
        return {
            "error": f"Failed to search documents: {str(e)}",
            "query": query,
            "results": [],
            "suggestion": "Check Pinecone configuration and try again.",
        }
