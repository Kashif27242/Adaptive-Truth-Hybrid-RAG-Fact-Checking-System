import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models import VerificationResult, Evidence
from retriever import search_web, search_local

async def verify_claim(claim: str) -> VerificationResult:
    # 1. Retrieve evidence
    local_evidence = search_local(claim)
    web_evidence = search_web(claim)
    all_evidence = local_evidence + web_evidence
    
    # 2. Prepare context
    context_str = "\n".join([f"- [{e.source}] {e.text}" for e in all_evidence])
    
    # 3. Adjudicate with Gemini
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
    You are an expert fact-checker. Verify the following claim based ONLY on the provided evidence.
    
    Claim: {claim}
    
    Evidence:
    {context}
    
    Instructions:
    1. Determine if the claim is Supported, Refuted, or NotEnoughInfo.
    2. Provide a brief reasoning.
    3. If evidence is conflicting, prioritize more recent or reliable sources (Web > Local if Local is outdated).
    
    Output format:
    Verdict: [Verdict]
    Reasoning: [Reasoning]
    """)
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"claim": claim, "context": context_str})
        content = response.content
        
        # Handle cases where content might be a list or object
        if not isinstance(content, str):
            content = str(content)
            
        # Simple parsing (robustness can be improved)
        verdict = "NotEnoughInfo"
        reasoning = content
        
        if "Verdict: Supported" in content:
            verdict = "Supported"
        elif "Verdict: Refuted" in content:
            verdict = "Refuted"
            
        return VerificationResult(
            claim=claim,
            verdict=verdict,
            reasoning=reasoning,
            evidence=all_evidence
        )
    except Exception as e:
        return VerificationResult(
            claim=claim,
            verdict="Error",
            reasoning=f"LLM Error: {str(e)}",
            evidence=all_evidence
        )
