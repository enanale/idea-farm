/**
 * Topic Navigation Component
 */

interface TopicNavProps {
    topics: string[];
    selectedTopic: string | null;
    onSelectTopic: (topic: string | null) => void;
}

export default function TopicNav({ topics, selectedTopic, onSelectTopic }: TopicNavProps) {
    return (
        <nav className="topic-nav">
            <h2>Topics</h2>
            <ul>
                <li>
                    <button
                        className={`topic-btn ${selectedTopic === null ? 'active' : ''}`}
                        onClick={() => onSelectTopic(null)}
                    >
                        All Ideas
                    </button>
                </li>
                {topics.map((topic) => (
                    <li key={topic}>
                        <button
                            className={`topic-btn ${selectedTopic === topic ? 'active' : ''}`}
                            onClick={() => onSelectTopic(topic)}
                        >
                            {topic}
                        </button>
                    </li>
                ))}
            </ul>
        </nav>
    );
}
