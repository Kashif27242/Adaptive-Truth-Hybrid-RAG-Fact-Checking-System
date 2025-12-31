import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models import VerificationResult, Evidence
from retriever import search_web, search_local

async def verify_claim(claim: str) -> VerificationResult:
    # --- Step 1: Query Router (LLM Agent) ---
    print(f"Agent: Analyzing claim: '{claim}'")
    
    # Initialize the Router LLM (Fast model)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return VerificationResult(claim=claim, verdict="Error", reasoning="Missing API Key", evidence=[])

    router_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=api_key)
    
    # Ask the router if we need external info
    router_prompt = ChatPromptTemplate.from_template("""
    You are a Query Router for a fact-checking system.
    Your job is to decide if the following claim requires a **Google Search** (Live Web) or if it can be answered by a **Static Knowledge Base** (Historical/General Facts up to 2023).
    
    Claim: "{claim}"
    
    Rules:
    - IF the claim is about a recent event (2024, 2025, "today", "yesterday", "breaking news"), RETURN "WEB".
    - IF the claim is something that might have changed recently (e.g. "Is Person X alive?"), RETURN "WEB".
    - IF the claim is a historical fact, scientific truth, or general knowledge (e.g. "Water is H2O", "Rome fell in 476"), RETURN "LOCAL".
    
    Return ONLY one word: "WEB" or "LOCAL".
    """)
    
    try:
        router_chain = router_prompt | router_llm
        route_decision = await router_chain.ainvoke({"claim": claim})
        route_decision = route_decision.content.strip().upper()
        print(f"Agent: Router decided -> {route_decision}")
    except Exception as e:
        print(f"Router Error: {e}. Defaulting to WEB.")
        route_decision = "WEB"

    # Execute Search based on Router
    local_evidence = []
    web_evidence = []
    
    if route_decision == "LOCAL":
        # Search Local ONLY first
        print("Agent: Routing to Local DB...")
        local_evidence = search_local(claim)
        
        # Fallback: If local result is poor, upgrade to Web
        if not local_evidence or local_evidence[0].confidence < 0.4:
            print("Agent: Local evidence weak. Falling back to Web Search.")
            web_evidence = search_web(claim)
            
    else: # route_decision == "WEB"
        print("Agent: Routing to Web Search (Time-Sensitive/Dynamic)...")
        # We search BOTH for context, but prioritize Web in adjudication
        web_evidence = search_web(claim)
        # Optional: Search local too just to see if we have background info?
        # Let's search local too, it's cheap (local DB).
        local_evidence = search_local(claim)  
    
    all_evidence = local_evidence + web_evidence
    
    # --- Step 3: The Adjudicator (Reasoning Engine) ---
    # Prepare context
    context_str = "\n".join([f"- [{e.source}] (Confidence: {e.confidence:.2f}) {e.text}" for e in all_evidence])
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return VerificationResult(
            claim=claim, 
            verdict="Error", 
            reasoning="Missing GOOGLE_API_KEY", 
            evidence=all_evidence
        )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=api_key)
    
    prompt = ChatPromptTemplate.from_template("""
    You are an expert fact-checker in an "Adaptive Truth" system. 
    Your goal is to verify the claim based ONLY on the provided evidence.
    
    Claim: {claim}
    
    Evidence:
    {context}
    
    Critical Instructions for Adjudication:
    1. **Source Weighting**: 
       - "Local (ChromaDB)" contains established valid facts (FEVER dataset). Trust this for general knowledge.
       - "Web" contains live internet results. Trust this for **recent events** (post-2023) or if Local DB is silent.
    2. **Conflict Resolution**:
       - IF Local says X and Web says Y:
         - If the claim is about a static scientific/historical fact, prioritize Local.
         - If the claim is about a changing status (e.g., "Person X is dead"), prioritize the Web (Time-Sensitive).
    3. **Verdict Categories**:
       - Supported: Evidence clearly confirms the claim.
       - Refuted: Evidence clearly contradicts the claim.
       - NotEnoughInfo: Neither source provides sufficient proof.
    
    Output format:
    Verdict: [Supported/Refuted/NotEnoughInfo]
    Reasoning: [Concise explanation of how you weighed the evidence and reached the verdict. Explicitly mention if you prioritized Web over Local due to recency.]
    """)
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"claim": claim, "context": context_str})
        content = response.content
        
        if not isinstance(content, str):
            content = str(content)
            
        verdict = "NotEnoughInfo"
        if "Verdict: Supported" in content:
            verdict = "Supported"
        elif "Verdict: Refuted" in content:
            verdict = "Refuted"
            
        return VerificationResult(
            claim=claim,
            verdict=verdict,
            reasoning=content, # Return full content as it includes reasoning
            evidence=all_evidence
        )
    except Exception as e:
        return VerificationResult(
            claim=claim,
            verdict="Error",
            reasoning=f"LLM Error: {str(e)}",
            evidence=all_evidence
        )
