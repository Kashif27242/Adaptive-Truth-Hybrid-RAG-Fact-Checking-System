import React from 'react';

const VerificationResult = ({ result }) => {
    if (!result) return null;

    const { verdict, reasoning, evidence } = result;

    const getStatusClass = (v) => {
        switch (v.toLowerCase()) {
            case 'supported': return 'status-supported';
            case 'refuted': return 'status-refuted';
            default: return 'status-uncertain';
        }
    };

    return (
        <div className="card result-container animate-fade-in">
            <div className="result-status">
                <span className={`status-badge ${getStatusClass(verdict)}`}>
                    {verdict}
                </span>
                <h2>Verification Analysis</h2>
            </div>

            <div className="reasoning">
                <strong>AI Reasoning:</strong>
                <p>{reasoning}</p>
            </div>

            <div className="evidence-section">
                <h3>Supporting Evidence</h3>
                <div className="evidence-grid">
                    {evidence.map((item, index) => (
                        <div key={index} className="evidence-card">
                            <span className="evidence-source">
                                {(item.source.toLowerCase().includes('local') || item.source.toLowerCase().includes('chroma') || item.source.includes('Pinecone')) ? '📂 Local Knowledge' : '🌐 Web Search'}
                            </span>
                            <p className="evidence-text">"{item.text}"</p>
                            {item.url && (
                                <a
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ color: 'var(--accent-primary)', fontSize: '0.9rem' }}
                                >
                                    View Source
                                </a>
                            )}
                            <div className="confidence-bar" title={`Confidence: ${item.confidence}`}>
                                <div
                                    className="confidence-fill"
                                    style={{ width: `${item.confidence * 100}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default VerificationResult;
