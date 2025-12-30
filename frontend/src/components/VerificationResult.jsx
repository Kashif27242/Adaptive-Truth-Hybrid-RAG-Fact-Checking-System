import React from 'react';

const VerificationResult = ({ result }) => {
    if (!result) return null;

    const { verdict, reasoning, evidence } = result;

    const getVerdictColor = (v) => {
        switch (v.toLowerCase()) {
            case 'supported': return 'green';
            case 'refuted': return 'red';
            default: return 'orange';
        }
    };

    return (
        <div className="result-container">
            <h2>Verdict: <span style={{ color: getVerdictColor(verdict) }}>{verdict}</span></h2>
            <p className="reasoning">{reasoning}</p>

            <h3>Evidence:</h3>
            <ul>
                {evidence.map((item, index) => (
                    <li key={index}>
                        <strong>[{item.source}]</strong> {item.text}
                        {item.url && <a href={item.url} target="_blank" rel="noopener noreferrer"> (Link)</a>}
                        <br />
                        <small>Confidence: {item.confidence}</small>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default VerificationResult;
