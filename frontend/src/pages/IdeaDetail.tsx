/**
 * Idea Detail Page - Full view of a single idea
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../lib/api';
import type { Idea } from '../lib/api';

export default function IdeaDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [idea, setIdea] = useState<Idea | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadIdea = async () => {
      if (!id) return;
      
      try {
        const response = await api.getIdea(id);
        setIdea(response.idea);
      } catch (err) {
        setError('Failed to load idea');
      } finally {
        setLoading(false);
      }
    };

    loadIdea();
  }, [id]);

  const handleDelete = async () => {
    if (!id || !confirm('Are you sure you want to delete this idea?')) return;
    
    try {
      await api.deleteIdea(id);
      navigate('/');
    } catch (err) {
      setError('Failed to delete idea');
    }
  };

  if (loading) {
    return <div className="loading-page">Loading...</div>;
  }

  if (error || !idea) {
    return (
      <div className="error-page">
        <p>{error || 'Idea not found'}</p>
        <Link to="/">Back to Home</Link>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    pending: 'status-pending',
    processing: 'status-processing',
    ready: 'status-ready',
    failed: 'status-failed',
  };

  return (
    <div className="idea-detail-page">
      <header className="detail-header">
        <Link to="/" className="back-link">← Back to Ideas</Link>
        <button onClick={handleDelete} className="btn-danger">Delete</button>
      </header>

      <main className="detail-content">
        <div className="detail-meta">
          <span className={`status-badge ${statusColors[idea.status]}`}>
            {idea.status}
          </span>
          {idea.topic && <span className="topic-badge">{idea.topic}</span>}
          <span className="detail-date">
            Saved on {new Date(idea.createdAt).toLocaleDateString()}
          </span>
        </div>

        <section className="detail-section">
          <h2>Original {idea.inputType === 'url' ? 'Link' : 'Idea'}</h2>
          {idea.inputType === 'url' ? (
            <a href={idea.originalContent} target="_blank" rel="noopener noreferrer" className="original-link">
              {idea.originalContent}
            </a>
          ) : (
            <p className="original-text">{idea.originalContent}</p>
          )}
        </section>

        {idea.summary ? (
          <section className="detail-section">
            <h2>Summary</h2>
            <div className="summary-content">
              {idea.summary.split('\n').map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))}
            </div>
          </section>
        ) : idea.status === 'pending' || idea.status === 'processing' ? (
          <section className="detail-section">
            <h2>Summary</h2>
            <div className="processing-message">
              <div className="spinner"></div>
              <p>Processing your idea... This may take a moment.</p>
            </div>
          </section>
        ) : null}

        {idea.suggestedLinks && idea.suggestedLinks.length > 0 && (
          <section className="detail-section">
            <h2>Explore Further</h2>
            <ul className="suggested-links">
              {idea.suggestedLinks.map((link, i) => (
                <li key={i}>
                  <a href={link.url} target="_blank" rel="noopener noreferrer">
                    <strong>{link.title}</strong>
                    <p>{link.description}</p>
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
