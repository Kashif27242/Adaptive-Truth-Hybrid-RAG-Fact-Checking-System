import React, { useState } from 'react';

const VerificationResult = ({ result }) => {
    const [showEvidence, setShowEvidence] = useState(false);

    if (!result) return null;

    const { verdict, reasoning, evidence } = result;

    // Determine primary source
    const hasWeb = evidence.some(e => e.source.toLowerCase().includes('web') || e.source.toLowerCase().includes('http'));
    const sourceLabel = hasWeb ? "Live Web Search" : "Local Verified Knowledge";
    const sourceIcon = hasWeb ? "🌐" : "📚";

    const getStatusClass = (v) => {
        switch (v.toLowerCase()) {
            case 'supported': return 'status-supported';
            case 'refuted': return 'status-refuted';
            default: return 'status-uncertain';
        }
    };

    return (
        <div className="card result-container animate-fade-in">
            {/* Header Section */}
            <div className="result-header" style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div
                    className={`status-badge ${getStatusClass(verdict)}`}
                    style={{
                        fontSize: '1.5rem',
                        padding: '0.75rem 2rem',
                        display: 'inline-block',
                        marginBottom: '1rem',
                        boxShadow: '0 0 20px rgba(0,0,0,0.2)'
                    }}
                >
                    {verdict}
                </div>
            </div>

            {/* Reasoning Section */}
            <div className="reasoning">
                <h3 style={{ marginBottom: '1rem', color: 'var(--accent-primary)' }}>AI Analysis</h3>
                <p style={{ lineHeight: '1.8', fontSize: '1.1rem' }}>{reasoning}</p>
            </div>

            {/* Evidence Toggle */}
            <div className="evidence-section" style={{ marginTop: '2rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <button
                    onClick={() => setShowEvidence(!showEvidence)}
                    style={{
                        background: 'transparent',
                        border: '1px solid var(--border-color)',
                        width: '100%',
                        color: 'var(--text-secondary)',
                        fontSize: '0.9rem'
                    }}
                >
                    {showEvidence ? "Hide Raw Evidence Details" : "View Supporting Evidence Sources"}
                </button>

                {showEvidence && (
                    <div className="evidence-grid animate-fade-in" style={{ marginTop: '1.5rem' }}>
                        {evidence.map((item, index) => (
                            <div key={index} className="evidence-card">
                                <span className="evidence-source">
                                    {(item.source.toLowerCase().includes('local') || item.source.toLowerCase().includes('chroma')) ? '📂 Local Knowledge' : '🌐 Web Search'}
                                </span>
                                <p className="evidence-text">"{item.text}"</p>
                                {item.url && (
                                    <a
                                        href={item.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{ color: 'var(--accent-primary)', fontSize: '0.9rem', display: 'block', marginTop: '0.5rem' }}
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
                )}
            </div>
        </div>
    );
};

export default VerificationResult;
