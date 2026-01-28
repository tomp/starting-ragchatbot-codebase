# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Retrieval-Augmented Generation (RAG) system** for educational course materials. It combines ChromaDB vector search with Anthropic's Claude API using a tool-based architecture where Claude decides when to search course content.

**Key Architecture Pattern**: Tool-based RAG with two-phase AI generation:
1. Claude receives user query and decides whether to use the search tool
2. If search is needed, tool executes and returns formatted results
3. Claude synthesizes final answer from search results

## Important: Virtual Environment Management

**Always use `uv` to manage the virtual environment for this project.** Do not use `pip`, `venv`, `virtualenv`, or other Python package managers. All dependency management and Python execution should go through `uv`.

## Development Commands

### Running the Application
```bash
./run.sh                                    # Start server on port 8000
cd backend && uv run uvicorn app:app --reload --port 8000  # Manual start
```

### Dependency Management
```bash
uv sync                                     # Install/update dependencies
uv add <package>                            # Add new dependency
uv run <command>                            # Run any Python command in managed environment
```

**Note**: Never use `pip install` or create manual virtual environments. Use `uv` for all operations.

### Environment Setup
```bash
cp .env.example .env                        # Create environment file
# Edit .env and set ANTHROPIC_API_KEY
```

### Clearing Vector Database
```bash
rm -rf backend/chroma_db/                   # Delete ChromaDB storage
# Server will rebuild on next startup
```

## Architecture Deep Dive

### Request Flow (Critical Understanding)

**User Query → Two Claude API Calls → Response**

1. **Frontend** (`frontend/script.js`): `POST /api/query` with `{query, session_id}`
2. **API Layer** (`backend/app.py:56`): Creates session if needed, calls RAG system
3. **RAG Orchestrator** (`backend/rag_system.py:102`): Coordinates all components
4. **Session Manager** (`backend/session_manager.py`): Retrieves conversation history (max 2 exchanges)
5. **AI Generator - First Call** (`backend/ai_generator.py:43`):
   - Builds system prompt with conversation context
   - Calls Claude API with tools enabled (`tool_choice: auto`)
   - Claude decides if search is needed (returns `stop_reason: "tool_use"`)
6. **Tool Execution** (`backend/search_tools.py:52`):
   - ToolManager executes `CourseSearchTool`
   - Calls `VectorStore.search()` with query, optional course_name, lesson_number
7. **Vector Search** (`backend/vector_store.py:61`):
   - **Two ChromaDB collections**: `course_catalog` (metadata) + `course_content` (chunks)
   - If `course_name` provided: semantic search in catalog to resolve exact title
   - Build filter dict from course_title and/or lesson_number
   - Query `course_content` with filters, returns top 5 chunks
8. **Result Formatting** (`backend/search_tools.py:88`):
   - Formats chunks with headers: `[Course Title - Lesson N]`
   - Stores sources in `last_sources` for UI display
9. **AI Generator - Second Call** (`backend/ai_generator.py:89`):
   - Builds message array: user query → assistant tool_use → user tool_result
   - Calls Claude API **without tools** (prevents infinite loops)
   - Claude synthesizes answer from search results
10. **Post-Processing** (`backend/rag_system.py:130-137`):
    - Extracts sources from tool manager
    - Updates session history with exchange
    - Returns `(answer, sources)` tuple
11. **Frontend Display** (`frontend/script.js:85`): Renders markdown with collapsible sources

### Component Responsibilities

**`rag_system.py`** - Central orchestrator, owns no business logic:
- Initializes all components with config
- Registers search tool with ToolManager
- Coordinates query flow between AI generator, session manager, and tool manager
- Extracts and resets sources after each query

**`ai_generator.py`** - Claude API wrapper with tool execution loop:
- Static `SYSTEM_PROMPT` defines behavior: use tool for course questions, no meta-commentary
- First call: Claude decides tool use (`temperature=0`, `max_tokens=800`)
- `_handle_tool_execution()`: Executes tools and makes second API call
- Second call: Always without tools to prevent loops

**`search_tools.py`** - Tool abstraction layer:
- `Tool` ABC: `get_tool_definition()` + `execute()` interface
- `CourseSearchTool`: Implements Anthropic tool schema, calls vector store
- `ToolManager`: Registry pattern, tracks sources across tools via `last_sources`

**`vector_store.py`** - ChromaDB abstraction with dual collections:
- `course_catalog`: Stores course titles/metadata, used for semantic course name resolution
- `course_content`: Stores text chunks with metadata (course_title, lesson_number, chunk_index)
- `_resolve_course_name()`: Fuzzy matching via vector similarity (e.g., "MCP" → "Model Context Protocol")
- `_build_filter()`: Constructs ChromaDB `where` clauses for course/lesson filtering

**`document_processor.py`** - Text chunking with context preservation:
- Parses metadata: `Course Title:`, `Course Link:`, `Course Instructor:`
- Detects lessons: regex `r'^Lesson\s+(\d+):\s*(.+)$'`
- Sentence-based chunking (800 chars, 100 char overlap) with abbreviation handling
- **Critical**: Adds context prefix to chunks: `"Lesson {N} content: {text}"` or `"Course {title} Lesson {N} content: {text}"`

**`session_manager.py`** - Conversation context:
- Stores last `MAX_HISTORY * 2` messages (default: 2 exchanges = 4 messages)
- Formats as `"User: {msg}\nAssistant: {msg}"` string for system prompt

### Data Flow Patterns

**Course Loading** (startup event in `app.py:88`):
```python
add_course_folder(docs_path)
  → DocumentProcessor.process_course_document()  # Returns (Course, List[CourseChunk])
  → VectorStore.add_course_metadata()            # Adds to course_catalog
  → VectorStore.add_course_content()             # Adds chunks to course_content
```

**Vector Search with Filtering**:
```python
VectorStore.search(query="MCP servers", course_name="Introduction", lesson_number=2)
  → _resolve_course_name("Introduction")         # Returns exact title via semantic search
  → _build_filter(exact_title, 2)                # {"$and": [{course_title}, {lesson_number}]}
  → ChromaDB.query(query_texts, where=filter)    # Filtered vector similarity
  → SearchResults(documents, metadata, distances)
```

**Tool Source Tracking** (for UI display):
```python
CourseSearchTool._format_results()
  → self.last_sources = ["Course - Lesson 1", ...]  # Store during formatting
RAGSystem.query()
  → sources = tool_manager.get_last_sources()        # Retrieve after AI response
  → tool_manager.reset_sources()                     # Clear for next query
```

## Configuration (backend/config.py)

All config loaded from environment + hardcoded defaults:
- `ANTHROPIC_API_KEY`: Required, from `.env`
- `ANTHROPIC_MODEL`: `"claude-sonnet-4-20250514"`
- `EMBEDDING_MODEL`: `"all-MiniLM-L6-v2"` (Sentence Transformers)
- `CHUNK_SIZE`: 800 characters
- `CHUNK_OVERLAP`: 100 characters
- `MAX_RESULTS`: 5 search results
- `MAX_HISTORY`: 2 conversation exchanges
- `CHROMA_PATH`: `"./chroma_db"` (relative to backend/)

## Common Modification Patterns

### Adding a New Tool

1. Create class inheriting from `Tool` in `search_tools.py`
2. Implement `get_tool_definition()` with Anthropic schema
3. Implement `execute(**kwargs)` with tool logic
4. Register in `rag_system.py:24`: `self.tool_manager.register_tool(YourTool())`

### Changing Search Behavior

**Vector Store** (`vector_store.py`):
- Adjust `MAX_RESULTS` in config for more/fewer chunks
- Modify `_build_filter()` to add new metadata filters
- Add new collections in `__init__()` for different search types

**Search Tool** (`search_tools.py`):
- Update `input_schema` to accept new parameters
- Modify `_format_results()` to change result presentation
- Change source tracking logic in `last_sources`

### Modifying AI Behavior

**System Prompt** (`ai_generator.py:8-30`):
- `SYSTEM_PROMPT` is static and defines Claude's behavior
- Controls when to search, response style, meta-commentary rules
- Injected with conversation history on each call

**API Parameters** (`ai_generator.py:37-40`):
- `temperature`: Currently 0 (deterministic), increase for creativity
- `max_tokens`: Currently 800, adjust for longer responses
- Model can be changed in config

### Document Processing Changes

**Chunk Size/Overlap** (`document_processor.py:25-91`):
- Modify `CHUNK_SIZE`/`CHUNK_OVERLAP` in config
- Sentence-based algorithm in `chunk_text()` respects natural breaks
- Change context prefix in `process_course_document():184-234`

**Metadata Extraction** (`document_processor.py:110-146`):
- Expected format: `Course Title:`, `Course Link:`, `Course Instructor:` in first 4 lines
- Lesson markers: `Lesson N: Title` followed by optional `Lesson Link:`
- Modify regexes to support different formats

## Critical Implementation Details

### Why Two API Calls?

The architecture uses two separate Claude API calls to implement tool-based RAG:
1. **First call**: Claude analyzes query and decides if search is needed (returns tool_use)
2. **Second call**: Claude synthesizes answer from tool results (no tools to prevent loops)

This pattern allows Claude to make intelligent decisions about when to search vs. answer from general knowledge.

### ChromaDB Collection Strategy

Two separate collections avoid metadata bloat and enable different query patterns:
- `course_catalog`: Small, optimized for course name fuzzy matching
- `course_content`: Large, optimized for semantic content search with filters

### Session History Management

History is formatted as a string (`"User: ...\nAssistant: ..."`) rather than messages array because it's injected into the system prompt, not the messages parameter. This preserves conversation context without complicating the tool execution flow.

### Source Tracking Pattern

Sources are tracked in the tool itself (`CourseSearchTool.last_sources`) because:
1. Formatting happens during tool execution
2. Sources needed for UI are derived from search metadata
3. ToolManager provides centralized access via `get_last_sources()`
4. Reset after each query prevents leakage between requests

## File Locations Quick Reference

- **Entry point**: `backend/app.py` (FastAPI app)
- **Core logic**: `backend/rag_system.py` (orchestrator)
- **AI interface**: `backend/ai_generator.py` (Claude API wrapper)
- **Search**: `backend/vector_store.py` + `backend/search_tools.py`
- **Document processing**: `backend/document_processor.py`
- **Frontend**: `frontend/index.html`, `frontend/script.js`, `frontend/style.css`
- **Config**: `backend/config.py` + `.env`
- **Course data**: `docs/*.txt` (processed on startup)
- **Vector DB**: `backend/chroma_db/` (auto-created, gitignored)

## Dependencies

Package manager: **uv** (modern Python package manager)
- FastAPI 0.116.1 (web framework)
- Uvicorn 0.35.0 (ASGI server)
- ChromaDB 1.0.15 (vector database)
- Anthropic 0.58.2 (Claude API client)
- Sentence Transformers 5.0.0 (embeddings)
- python-dotenv 1.1.1 (environment variables)

Python requirement: >=3.13 (specified in `.python-version` and `pyproject.toml`)
