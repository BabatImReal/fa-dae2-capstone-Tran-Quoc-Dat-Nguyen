# PDF Upload Feature - Testing Guide

## ✅ Feature Implemented

Your Chainlit app now supports **automatic PDF upload, chunking, and embedding** for RAG!

## 🎯 What's New

### 1. **Upload at Chat Start**
- When you start a new chat, you'll see a prompt to upload PDFs
- Upload up to 5 PDFs (max 20MB each)
- Click "Skip" to continue without uploading

### 2. **Upload During Chat**
- Click the 📎 attachment icon while chatting
- Upload PDFs at any time during the conversation
- Immediately available for search after processing

### 3. **Automatic Processing Pipeline**

```
PDF Upload
    ↓
Text Extraction (pdfplumber)
    ↓
Chunking (1000 chars, 200 overlap, sentence-based)
    ↓
Dense Embedding (Pinecone llama-text-embed-v2) - Semantic
    ↓
Sparse Embedding (Pinecone sparse-english-v0) - Lexical/Keyword
    ↓
Storage in BOTH Pinecone indexes (dense + sparse)
    ↓
Ready for Hybrid RAG Search! 🚀
```

## 🔧 How It Works

### Backend Components Used:
1. **DocumentProcessor** (`ai-agent/rag/service/document_processor.py`)
   - Handles text extraction
   - Cleans and normalizes text
   - Creates chunks with metadata

2. **PineconeEmbedder** (`ai-agent/rag/embed_and_store.py`)
   - Generates DENSE embeddings (semantic) using Pinecone's inference API
   - Stores vectors in Pinecone dense index with metadata

3. **SparseEmbedder** (`ai-agent/rag/sparse_embedder.py`)
   - Generates SPARSE embeddings (lexical/keyword) using Pinecone's sparse model
   - Stores vectors in Pinecone sparse index with metadata

4. **Chainlit Integration** (`ai-agent/chainlit/chainlit_app.py`)
   - File upload UI
   - Progress messages
   - Async processing of both embedding types

## 📝 Example Usage

### Test Flow:
1. **Start the Chainlit app**
   ```bash
   chainlit run ai-agent/chainlit/chainlit_app.py
   ```

2. **Upload a PDF**
   - See the upload prompt
   - Select a PDF from your computer
   - Watch the processing steps:
     - 📄 Processing PDF...
     - ✅ Extracted and chunked into X chunks
     - 🔄 Generating dense embeddings (semantic)...
     - 🔄 Generating sparse embeddings (lexical)...
     - 💾 Storing dense vectors (semantic index)...
     - 💾 Storing sparse vectors (lexical index)...
     - ✅ Successfully processed!
       - Dense vectors: ✅ Stored
       - Sparse vectors: ✅ Stored

3. **Search the uploaded content**
   ```
   User: "What is mentioned about [topic in your PDF]?"
   Agent: [Uses hybrid_search_documents to find relevant chunks]
   ```

## 🔍 Search Configuration

The uploaded PDFs are stored in **namespaces** based on their filename:
- `my_document.pdf` → namespace: `my_document`
- `Sales Report 2024.pdf` → namespace: `sales_report_2024`

**Dual Index Storage:**
- **Dense Index** (PINECONE_DENSE_INDEX_NAME): Semantic/contextual embeddings
- **Sparse Index** (PINECONE_SPARSE_INDEX_NAME): Lexical/keyword embeddings

The RAG tools automatically search both indexes:
- `hybrid_search_documents` ✅ **RECOMMENDED** - Combines dense + sparse with reranking
- `search_documents` - Dense only (semantic search)

## ⚙️ Customization Options

You can modify these settings in `process_pdf_upload()`:

```python
processor = DocumentProcessor(
    chunk_size=1000,          # Adjust chunk size
    chunk_overlap=200,        # Adjust overlap
    chunking_strategy="sentence",  # or "fixed", "paragraph"
    language="en"             # Document language
)
```

## 🚨 Error Handling

The system handles:
- ❌ Invalid PDFs (no text extracted)
- ❌ Processing errors (extraction, embedding, storage)
- ❌ File size limits (20MB per file)
- ❌ File type validation (PDF only)

## 🎉 Benefits

1. **No Manual Processing** - Just upload and go!
2. **Dual Embedding Strategy** - Semantic (meaning) + Lexical (keywords)
3. **Automatic Chunking** - Optimized for RAG
4. **Smart Embeddings** - Uses Pinecone's inference API (both models)
5. **Organized Storage** - Namespace-based organization in both indexes
6. **Immediate Availability** - Search right after upload
7. **Hybrid Search Ready** - Best quality results with combined approach

## 📊 Metadata Tracked

Each chunk includes:
- `source`: Original filename
- `chunk_index`: Position in document
- `total_chunks`: Total chunks from document
- `chunk_size`: Character count
- `chunk_size_tokens`: Rough token count
- `timestamp`: Processing time
- `document_type`: File extension
- `language`: Document language
- `chunking_strategy`: Strategy used

## 🔐 Requirements

Make sure these environment variables are set:
```env
PINECONE_API_KEY=your_key
PINECONE_DENSE_INDEX_NAME=your_dense_index_name
PINECONE_SPARSE_INDEX_NAME=your_sparse_index_name
PINECONE_ENV=your_environment  # Optional
```

## ✨ Next Steps

1. Test with a sample PDF
2. Try searching the uploaded content
3. Upload multiple PDFs to build a knowledge base
4. Experiment with different chunking strategies
5. Use hybrid search for best results!

---

**Happy RAG-ing! 🚀**
