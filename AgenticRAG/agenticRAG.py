"""Agentic RAG over a tiny in-memory BM25 index.

Same shape as basicRAG.py but the retrieval target is a hardcoded list of
party-planning docs instead of the live web. Useful as a template for
pointing an agent at any local corpus (ticket exports, docs dumps, etc.).
"""
from langchain_community.docstore.document import Document
from langchain_community.retrievers import BM25Retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from smolagents import CodeAgent, LiteLLMModel, Tool


# --- Retriever tool ---------------------------------------------------------
# A smolagents.Tool wrapper around a BM25 retriever. The agent sees it as a
# single callable that takes a query string and returns formatted matches.

class PartyPlanningRetrieverTool(Tool):
    name = "party_planning_retriever"
    description = "Uses semantic search to retrieve relevant party planning ideas for Alfred’s superhero-themed party at Wayne Manor."
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. This should be a query related to party planning or superhero themes.",
        }
    }
    output_type = "string"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        # BM25 (lexical) is cheap and dependency-free. Swap for a vector
        # retriever when the corpus grows past a few hundred documents.
        self.retriever = BM25Retriever.from_documents(docs, k=5)

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"

        docs = self.retriever.invoke(query)
        # Numbered separators make it easy for the model to reference a
        # specific hit by index in its reasoning.
        return "\nRetrieved ideas:\n" + "".join(
            [
                f"\n\n===== Idea {str(i)} =====\n" + doc.page_content
                for i, doc in enumerate(docs)
            ]
        )


# --- Knowledge base ---------------------------------------------------------
# Hardcoded stand-in for what would normally be a loaded corpus of documents.
party_ideas = [
    {"text": "A superhero-themed masquerade ball with luxury decor, including gold accents and velvet curtains.", "source": "Party Ideas 1"},
    {"text": "Hire a professional DJ who can play themed music for superheroes like Batman and Wonder Woman.", "source": "Entertainment Ideas"},
    {"text": "For catering, serve dishes named after superheroes, like 'The Hulk's Green Smoothie' and 'Iron Man's Power Steak.'", "source": "Catering Ideas"},
    {"text": "Decorate with iconic superhero logos and projections of Gotham and other superhero cities around the venue.", "source": "Decoration Ideas"},
    {"text": "Interactive experiences with VR where guests can engage in superhero simulations or compete in themed games.", "source": "Entertainment Ideas"}
]

source_docs = [
    Document(page_content=doc["text"], metadata={"source": doc["source"]})
    for doc in party_ideas
]

# Chunking: BM25 can match on a chunk and the agent reads just that chunk.
# For these short strings chunking is a no-op, but the pipeline is the same
# shape you want when swapping in a real document set.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    add_start_index=True,
    strip_whitespace=True,
    separators=["\n\n", "\n", ".", " ", ""],
)
docs_processed = text_splitter.split_documents(source_docs)

party_planning_retriever = PartyPlanningRetrieverTool(docs_processed)


# --- Model ------------------------------------------------------------------
# qwen2.5-coder:7b over qwen2:7b: the coder variant is noticeably better at
# emitting valid tool calls instead of free-text.
model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5-coder:7b",
    api_base="http://127.0.0.1:11434",
    num_ctx=8192,
    max_tokens=2096,
    temperature=0.5,
    custom_role_conversions=None,
)


# --- Agent ------------------------------------------------------------------
agent = CodeAgent(tools=[party_planning_retriever], model=model)


# --- Run --------------------------------------------------------------------
response = agent.run(
    "Find ideas for a luxury superhero-themed party, including entertainment, catering, and decoration options."
)

print(response)