# backend/query_processing/rag.py
from backend.DB.database import SessionLocal
from backend.DB.models import Policy
from backend.query_processing.llm_layer import call_llm_for_rag
from sqlalchemy import or_ # Import or_ for flexible querying
import traceback # For detailed error logging

def query_policy_rag(user_query: str, policy_type: str = "Unknown", airline_code: str = "AI") -> str:
    """
    Retrieves relevant policy documents from the DB based on type and airline,
    then uses an LLM to generate an answer based on those documents.
    """
    session = SessionLocal()
    results = [] # Initialize results
    policy_docs = [] # Initialize policy_docs

    try:
        print(f"[RAG Debug] Attempting query for policy_type='{policy_type}', airline_code='{airline_code}'")
        # --- PRIMARY QUERY ---
        query_filter = [Policy.airline_code == airline_code]
        if policy_type != "Unknown":
            query_filter.append(Policy.policy_type.ilike(f"%{policy_type}%"))

        results = session.query(Policy.policy_text).filter(*query_filter).all()
        print(f"[RAG Debug] Primary query for {airline_code}/{policy_type} found {len(results)} results.")

        # --- REVISED FALLBACK LOGIC ---
        # Only fallback if the primary query yielded NO results for the specific airline/type
        if not results:
            # --- FALLBACK: Try Default Airline (AI) with the SAME Policy Type ---
            print(f"[RAG Debug] Fallback: No policy found for {airline_code}/{policy_type}. Trying default 'AI' with type '{policy_type}'.")
            # Build filter for default airline and original policy type
            fallback_filter = [Policy.airline_code == "AI"] # Use default airline
            if policy_type != "Unknown":
                 fallback_filter.append(Policy.policy_type.ilike(f"%{policy_type}%"))
            
            results = session.query(Policy.policy_text).filter(*fallback_filter).all()
            print(f"[RAG Debug] Fallback query for AI/{policy_type} found {len(results)} results.")
            
            # Final check: if still no results, give up gracefully
            if not results:
                 print(f"[RAG Error] No policies found even with fallback logic.")
                 # Provide a more informative message
                 not_found_msg = f"Sorry, I couldn't find information specifically about '{policy_type}' policies for {airline_code}."
                 if airline_code != "AI": # Add this if we fell back from a different airline
                     not_found_msg += f" I also couldn't find it for our default airline (AI)."
                 return not_found_msg

        # --- Process Results ---
        # Ensure results were actually found before processing
        if results:
            policy_docs = [text for text, in results] # Extract text from tuples
            print(f"[RAG Debug] Final retrieved docs ({len(policy_docs)}):")
            for i, doc in enumerate(policy_docs):
                print(f"  Doc {i+1}: {doc[:100]}...") # Print start of each doc
        else:
            # This case should ideally be caught by the final check above, but as a safeguard:
            print(f"[RAG Error] Logic error: Reached processing stage with no results.")
            return f"Sorry, I couldn't retrieve any policy documents for '{policy_type}' for {airline_code}."


        # Pass the retrieved documents and original query to the LLM
        # Ensure policy_docs is not empty before calling LLM
        if not policy_docs:
             # Safeguard return if somehow policy_docs ended up empty after checks
              return f"Sorry, I couldn't find any relevant policy documents for '{policy_type}' for {airline_code} to process."
              
        response = call_llm_for_rag(user_query, policy_docs)
        return response

    except Exception as e:
        print(f"[RAG Error] Exception during database query or LLM call: {e}")
        traceback.print_exc() # Print full traceback for the error in RAG
        return "Sorry, I encountered an error while retrieving the policy information."
    finally:
        session.close()

