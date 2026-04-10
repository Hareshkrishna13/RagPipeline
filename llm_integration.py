"""Demo script showing LLM integration with LangGraph pipeline."""

import sys

from main_langgraph import DocumentPipelineGraph, display_results_with_summary

sys.stdout.reconfigure(encoding="utf-8")

print("\n" + "=" * 80)
print("LANGGRAPH WITH LLM INTEGRATION")
print("=" * 80)

# Initialize pipeline (this will use LLM from .env or defaults)
pipeline = DocumentPipelineGraph()

print("\nStep 1: Checking LLM Configuration...")
print("-" * 80)
print(f"LLM Model: {pipeline.llm.model_name}")
print(f"LLM Provider: {pipeline.llm.__class__.__name__}")
print("Ready to generate summaries!\n")

print("Step 2: Processing financial_report_pages.pdf...")
print("-" * 80)
success = pipeline.process_document("financial_report_pages.pdf")

if success:
    print("[OK] PDF processed successfully!\n")

    print("Step 3: Semantic Search with AI Summaries")
    print("=" * 80)

    queries = [
        "financial performance",
        "profit margins",
        "quarterly results",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\nSearch {i}: '{query}'")
        print("-" * 80)
        results, summary = pipeline.search_with_summary(query, top_k=2)

        if results:
            display_results_with_summary(results, summary)
        else:
            print("No results found.\n")

    print("\n" + "=" * 80)
    print("\nFeatures demonstrated:")
    print("  - LangGraph workflow with LLM integration")
    print("  - Semantic search with FAISS")
    print("  - AI-powered summarization using Claude/GPT/Groq")
    print("  - Multi-provider LLM support (Anthropic, OpenAI, Groq)")
    print("  - Environment-based configuration")
    print("\nSupported LLM Providers:")
    print("  - Anthropic Claude (claude-3-sonnet-20240229)")
    print("  - OpenAI GPT-4 (gpt-4, gpt-3.5-turbo)")
    print("  - Groq (mixtral-8x7b-32768, llama2-70b, gemma-7b-it)")
    print("\n")

else:
    print("[ERROR] Failed to process document")
