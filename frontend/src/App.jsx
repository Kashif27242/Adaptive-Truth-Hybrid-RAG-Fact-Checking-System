import React, { useState } from 'react';
import ClaimInput from './components/ClaimInput';
import VerificationResult from './components/VerificationResult';

function App() {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleVerify = async (claim) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ claim }),
      });

      if (!response.ok) {
        throw new Error('Failed to verify claim');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>Adaptive Truth</h1>
        <p>Hybrid RAG Fact-Checking System</p>
      </header>

      <main>
        <ClaimInput onVerify={handleVerify} isLoading={isLoading} />

        {error && (
          <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', marginTop: '2rem' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        <VerificationResult result={result} />
      </main>
    </div>
  );
}

export default App;
