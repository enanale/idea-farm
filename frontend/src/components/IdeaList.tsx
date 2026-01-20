/**
 * Idea List Component - Display saved ideas
 */

import { Link } from 'react-router-dom';
import type { Idea } from '../lib/api';

interface IdeaListProps {
  ideas: Idea[];
  onDelete: (id: string) => void;
}

export default function IdeaList({ ideas, onDelete }: IdeaListProps) {
  if (ideas.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🌱</div>
        <h3>No ideas yet</h3>
        <p>Paste a URL or type an idea above to get started.</p>
      </div>
    );
  }

  return (
    <div className="idea-list">
      {ideas.map((idea) => (
        <IdeaCard key={idea.id} idea={idea} onDelete={() => onDelete(idea.id)} />
      ))}
    </div>
  );
}

interface IdeaCardProps {
  idea: Idea;
  onDelete: () => void;
}

function IdeaCard({ idea, onDelete }: IdeaCardProps) {
  const statusColors: Record<string, string> = {
    pending: 'status-pending',
    processing: 'status-processing',
    ready: 'status-ready',
    failed: 'status-failed',
  };

  const truncateContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
    });
  };

  return (
    <div className="idea-card">
      <div className="idea-header">
        <span className={`status-badge ${statusColors[idea.status]}`}>
          {idea.status}
        </span>
        {idea.topic && <span className="topic-badge">{idea.topic}</span>}
        <span className="idea-date">{formatDate(idea.createdAt)}</span>
      </div>
      
      <div className="idea-content">
        {idea.inputType === 'url' ? (
          <a href={idea.originalContent} target="_blank" rel="noopener noreferrer" className="idea-link">
            {truncateContent(idea.originalContent)}
          </a>
        ) : (
          <p>{truncateContent(idea.originalContent)}</p>
        )}
      </div>
      
      {idea.summary && (
        <div className="idea-summary">
          <p>{truncateContent(idea.summary, 200)}</p>
        </div>
      )}
      
      <div className="idea-actions">
        <Link to={`/idea/${idea.id}`} className="btn-text">View Details</Link>
        <button onClick={onDelete} className="btn-text btn-danger">Delete</button>
      </div>
    </div>
  );
}
