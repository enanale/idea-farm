/**
 * API Client - Client-side Firestore implementation
 * Bypassing HTTP API for immediate responsiveness and simpler deployment
 */

import {
    collection,
    addDoc,
    getDoc,
    deleteDoc,
    updateDoc,
    query,
    where,
    orderBy,
    doc,
    serverTimestamp,
    onSnapshot
} from 'firebase/firestore';
import { db, auth } from './firebase';

export interface Idea {
    id: string;
    userId: string;
    inputType: 'url' | 'text';
    originalContent: string;
    driveFileId?: string | null;
    summary?: string | null;
    detailedAnalysis?: string | null;
    suggestedLinks?: Array<{ title: string; url: string; description: string }>;
    topic?: string | null;
    status: 'pending' | 'processing' | 'ready' | 'failed';
    createdAt: string;
    updatedAt: string;
}

export interface ListIdeasResponse {
    ideas: Idea[];
    grouped: Record<string, Idea[]>;
}

export interface SingleIdeaResponse {
    idea: Idea;
}

// Helper to check auth
const requireAuth = () => {
    if (!auth.currentUser) throw new Error('User not authenticated');
    return auth.currentUser.uid;
};

// Helper to convert Firestore dates to strings
const convertIdea = (docId: string, data: any): Idea => ({
    id: docId,
    ...data,
    createdAt: data.createdAt?.toDate?.().toISOString() || new Date().toISOString(),
    updatedAt: data.updatedAt?.toDate?.().toISOString() || new Date().toISOString(),
});

export const api = {
    /**
     * Subscribe to ideas (Real-time)
     */
    subscribeIdeas(topic: string | undefined, onUpdate: (response: ListIdeasResponse) => void, onError?: (error: Error) => void): () => void {
        const userId = requireAuth();
        let constraints = [
            where('userId', '==', userId),
            orderBy('createdAt', 'desc')
        ];

        if (topic) {
            constraints = [
                where('userId', '==', userId),
                where('topic', '==', topic),
                orderBy('createdAt', 'desc')
            ];
        }

        const q = query(collection(db, 'ideas'), ...constraints);

        return onSnapshot(q, (snapshot) => {
            const ideas = snapshot.docs.map(d => convertIdea(d.id, d.data()));
            const grouped: Record<string, Idea[]> = {};
            ideas.forEach(idea => {
                const t = idea.topic || 'Uncategorized';
                if (!grouped[t]) grouped[t] = [];
                grouped[t].push(idea);
            });
            onUpdate({ ideas, grouped });
        }, (error) => {
            if (onError) onError(error);
        });
    },

    /**
     * Get all ideas for the current user
     */
    async listIdeas(topic?: string): Promise<ListIdeasResponse> {
        return new Promise((resolve, reject) => {
            const unsubscribe = this.subscribeIdeas(topic, (response) => {
                unsubscribe();
                resolve(response);
            }, reject);
        });
    },

    /**
     * Create a new idea
     */
    async createIdea(content: string): Promise<SingleIdeaResponse> {
        const userId = requireAuth();
        const inputType = content.startsWith('http') ? 'url' : 'text';

        const ideaData = {
            userId,
            inputType,
            originalContent: content,
            status: 'pending',
            driveFileId: null,
            summary: null,
            suggestedLinks: [],
            topic: null,
            createdAt: serverTimestamp(),
            updatedAt: serverTimestamp()
        };

        const docRef = await addDoc(collection(db, 'ideas'), ideaData);

        // Return constructed object immediately
        return {
            idea: {
                id: docRef.id,
                ...ideaData,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            } as Idea
        };
    },

    /**
     * Get a single idea
     */
    async getIdea(id: string): Promise<SingleIdeaResponse> {
        const userId = requireAuth();
        const docRef = doc(db, 'ideas', id);
        const snap = await getDoc(docRef);

        if (!snap.exists()) {
            throw new Error('Idea not found');
        }

        const data = snap.data();
        if (data.userId !== userId) {
            throw new Error('Forbidden');
        }

        return { idea: convertIdea(snap.id, data) };
    },

    /**
     * Update an idea
     */
    async updateIdea(id: string, updates: Partial<Idea>): Promise<void> {
        const docRef = doc(db, 'ideas', id);
        await updateDoc(docRef, updates);
    },

    /**
     * Delete an idea
     */
    async deleteIdea(id: string): Promise<{ message: string }> {
        const userId = requireAuth();
        const docRef = doc(db, 'ideas', id);
        const snap = await getDoc(docRef);

        if (snap.exists()) {
            if (snap.data().userId !== userId) throw new Error('Forbidden');
            await deleteDoc(docRef);
        }

        return { message: 'Idea deleted' };
    }
};
