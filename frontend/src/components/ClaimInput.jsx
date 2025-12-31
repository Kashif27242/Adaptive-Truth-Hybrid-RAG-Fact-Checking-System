import React, { useState } from 'react';

const ClaimInput = ({ onVerify, isLoading }) => {
  const [claim, setClaim] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (claim.trim()) {
      onVerify(claim);
    }
  };

  return (
    <div className="claim-input-container input-card">
      <form onSubmit={handleSubmit} className="card">
        <textarea
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
          placeholder="Enter a claim to verify (e.g., 'The Queen is alive')..."
          rows={3}
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !claim.trim()}>
          {isLoading ? (
            <span>Running Agentic Verification...</span>
          ) : (
            'Verify Claim'
          )}
        </button>
      </form>
    </div>
  );
};

export default ClaimInput;
