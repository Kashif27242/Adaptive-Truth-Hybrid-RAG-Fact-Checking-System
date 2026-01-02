import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models import VerificationResult, Evidence
from retriever import search_web, search_local

async def verify_claim(claim: str) -> VerificationResult:
    # --- Step 1: Local First Strategy ---
    print(f"Agent: Analyzing claim: '{claim}'")
    
    # 1. Search Local Knowledge Base
    print("Agent: Querying Local DB (Chroma)...")
    local_evidence = search_local(claim)
    
    # 2. Adjudicate with ONLY Local Evidence first
    # We only skip this if we found literally 0 evidence, but search_local usually returns something or a specific 'no info' signal.
    # But let's verify what search_local returns. It returns a list of Evidence.
    
    verification_result = await _adjudicate_claim(claim, local_evidence, source_type="Local")
    
    # --- Step 2: Fallback to Web if Needed ---
    # Strategies for fallback:
    # A) Verdict is "NotEnoughInfo"
    # B) Verdict is "Refuted" but confidence is low (not implemented yet, stick to A)
    # C) Local evidence list was actually empty (handled by Adjudicator saying NotEnoughInfo)
    
    if verification_result.verdict == "NotEnoughInfo":
        print("Agent: Local verdict inconclusive. Falling back to Web Search...")
        
        web_evidence = search_web(claim)
        
        # Combine Evidence:
        # We assume local was insufficient, but maybe it had *some* useful context? 
        # Let's keep it.
        all_evidence = local_evidence + web_evidence
        
        # 3. Adjudicate with Combined Evidence
        verification_result = await _adjudicate_claim(claim, all_evidence, source_type="Web+Local")
    else:
        print(f"Agent: Local evidence sufficient. Verdict: {verification_result.verdict}")
        
    return verification_result

async def _adjudicate_claim(claim: str, evidence: list[Evidence], source_type: str) -> VerificationResult:
    """Helper to run the Adjudicator LLM on a specific set of evidence."""
    
    if not evidence:
         return VerificationResult(
            claim=claim,
            verdict="NotEnoughInfo",
            reasoning=f"No evidence found in {source_type}.",
            evidence=[]
        )

    # Context String
    context_str = "\n".join([f"- [{e.source}] (Conf: {e.confidence:.2f}) {e.text}" for e in evidence])
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return VerificationResult(claim=claim, verdict="Error", reasoning="Missing API Key", evidence=evidence)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=api_key)
    
    # Prompt emphasizing the source we are looking at
    prompt = ChatPromptTemplate.from_template("""
    You are an expert fact-checker. Verify the claim based ONLY on the provided evidence.
    
    Claim: {claim}
    
    Evidence Source: {source_type}
    Evidence:
    {context}
    
    Instructions:
    1. Assess if the evidence **conclusively** supports or refutes the claim.
    2. If the evidence is irrelevant, vague, or missing, return 'NotEnoughInfo'.
    3. Be strict. Do not hallucinate.
    
    Output format:
    Verdict: [Supported/Refuted/NotEnoughInfo]
    Reasoning: [Concise explanation]
    """)
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"claim": claim, "context": context_str, "source_type": source_type})
        content = response.content
        
        if not isinstance(content, str):
            content = str(content)
            
        # Parse Verdict and Reasoning
        verdict = "NotEnoughInfo"
        reasoning_text = content
        
        # Simple parsing strategy: Look for "Verdict:" and "Reasoning:" markers
        import re
        
        # Extact Verdict
        verdict_match = re.search(r"Verdict:\s*(Supported|Refuted|NotEnoughInfo)", content, re.IGNORECASE)
        if verdict_match:
            verdict = verdict_match.group(1).strip()
            # Normalize casing
            if verdict.lower() == "supported": verdict = "Supported"
            elif verdict.lower() == "refuted": verdict = "Refuted"
            elif verdict.lower() == "notenoughinfo": verdict = "NotEnoughInfo"
            
        # Extract Reasoning (everything after Reasoning:)
        reasoning_match = re.search(r"Reasoning:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning_text = reasoning_match.group(1).strip()
        else:
            # Fallback: if no "Reasoning:" tag, try to remove the Verdict line from content
            if verdict_match:
                reasoning_text = content.replace(verdict_match.group(0), "").strip()
            
        return VerificationResult(
            claim=claim,
            verdict=verdict,
            reasoning=reasoning_text,
            evidence=evidence
        )
    except Exception as e:
        return VerificationResult(
            claim=claim,
            verdict="Error",
            reasoning=f"LLM Error: {str(e)}",
            evidence=evidence
        )
