/**
 * Idea Form Component - Capture new ideas
 */

import { useState, FormEvent } from 'react';
import { api } from '../lib/api';
import type { Idea } from '../lib/api';

interface IdeaFormProps {
  onIdeaCreated: (idea: Idea) => void;
}

export default function IdeaForm({ onIdeaCreated }: IdeaFormProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    
    setError('');
    setLoading(true);

    try {
      const response = await api.createIdea(content.trim());
      onIdeaCreated(response.idea);
      setContent('');
    } catch (err) {
      setError('Failed to save idea');
    } finally {
      setLoading(false);
    }
  };

  const isUrl = content.startsWith('http://') || content.startsWith('https://');

  return (
    <div className="idea-form-container">
      <form onSubmit={handleSubmit} className="idea-form">
        <div className="input-wrapper">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste a URL or type an idea..."
            rows={3}
            disabled={loading}
          />
          <div className="input-hint">
            {isUrl ? '🔗 URL detected' : '💭 Text idea'}
          </div>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        <button type="submit" className="btn-primary" disabled={loading || !content.trim()}>
          {loading ? 'Saving...' : 'Save Idea'}
        </button>
      </form>
    </div>
  );
}
