"""Test script for LangGraph document processing pipeline."""

from main_langgraph import DocumentPipelineGraph, display_results

# Initialize the pipeline
pipeline = DocumentPipelineGraph()

print("\n" + "=" * 80)
print("Processing financial_report_pages.pdf file with LangGraph...")
print("=" * 80)

# Process document
success = pipeline.process_document("financial_report_pages.pdf")

if success:
    print("\n[✓] Document processed successfully!")

    # Perform searches
    print("\n" + "=" * 80)
    print("Search Results")
    print("=" * 80)

    queries = [
        "financial report",
        "revenue and expenses",
        "quarterly performance",
    ]

    for query in queries:
        print(f"\n>>> Query: '{query}'")
        print("-" * 80)
        results = pipeline.search(query, top_k=2)
        display_results(results)
        print()

    # Save the index
    print("=" * 80)
    print("Saving index for future use...")
    pipeline.save_index("financial_report_index")
    print("[OK] Index saved!")

else:
    print("\n[X] Failed to process document")
