/**
 * Home Page - Main dashboard with idea list and form
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import IdeaForm from '../components/IdeaForm';
import IdeaList from '../components/IdeaList';
import TopicNav from '../components/TopicNav';
import { api } from '../lib/api';
import type { Idea } from '../lib/api';

export default function Home() {
  const { user, signOut } = useAuth();
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [grouped, setGrouped] = useState<Record<string, Idea[]>>({});
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    const unsubscribe = api.subscribeIdeas(
      selectedTopic || undefined,
      (response) => {
        setIdeas(response.ideas);
        setGrouped(response.grouped);
        setLoading(false);
        setError('');
      },
      (err) => {
        console.error('Subscription error:', err);
        setError('Failed to load ideas');
        setLoading(false);
      }
    );

    return () => unsubscribe();
  }, [selectedTopic]);

  const handleIdeaCreated = (newIdea: Idea) => {
    // Subscription handles the update automatically
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteIdea(id);
      // Subscription handles the update automatically
    } catch (err) {
      setError('Failed to delete idea');
    }
  };

  const topics = Object.keys(grouped);

  return (
    <div className="home-page">
      <header className="app-header">
        <div className="header-content">
          <h1>Idea Farm</h1>
          <div className="user-menu">
            <span className="user-email">{user?.email}</span>
            <button onClick={signOut} className="btn-secondary">Sign Out</button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <aside className="sidebar">
          <TopicNav
            topics={topics}
            selectedTopic={selectedTopic}
            onSelectTopic={setSelectedTopic}
          />
        </aside>

        <div className="content-area">
          <IdeaForm onIdeaCreated={handleIdeaCreated} />

          {error && <div className="error-message">{error}</div>}

          {loading ? (
            <div className="loading">Loading ideas...</div>
          ) : (
            <IdeaList
              ideas={selectedTopic ? (grouped[selectedTopic] || []) : ideas}
              onDelete={handleDelete}
            />
          )}
        </div>
      </main>
    </div>
  );
}
