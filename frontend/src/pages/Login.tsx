/**
 * Login Page Component - Google Sign-In
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useGoogleLogin, type CodeResponse } from '@react-oauth/google';
import { functions } from '../lib/firebase';
import { httpsCallable } from 'firebase/functions';

export default function Login() {
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { signInWithGoogle } = useAuth();
    const navigate = useNavigate();

    const [needsDriveConsent, setNeedsDriveConsent] = useState(false);


    const loginToDrive = useGoogleLogin({
        flow: 'auth-code',
        scope: 'https://www.googleapis.com/auth/drive.file',
        onSuccess: async (codeResponse: CodeResponse) => {
            console.log("✅ [Login] Drive Consent Success:", codeResponse);
            setLoading(true);
            try {
                // Exchange code in backend
                console.log("🔄 [Login] Exchanging auth code...");
                const exchangeFn = httpsCallable(functions, 'exchange_auth_code');
                const result = await exchangeFn({
                    code: codeResponse.code,
                    redirect_uri: window.location.origin
                });
                console.log("✅ [Login] Exchange Result:", result.data);

                // Navigate after successful exchange
                navigate('/');
            } catch (e) {
                console.error("❌ [Login] Exchange Failed:", e);
                setError('Failed to grant Drive access. Check console.');
                setLoading(false);
            }
        },
        onError: (errorResponse) => {
            console.error("❌ [Login] Drive Consent Error:", errorResponse);
            setLoading(false);
            setError('Drive permission denied. Check console.');
        }
    });

    const handleGoogleSignIn = async () => {
        setError('');
        setLoading(true);
        console.log("🚀 [Login] Starting Google Sign In...");

        try {
            await signInWithGoogle();
            console.log("✅ [Login] Firebase Auth Success. Preparing Drive Consent UI...");



            setNeedsDriveConsent(true);
            setLoading(false);

        } catch (err: unknown) {
            console.error("❌ [Login] Firebase Auth Failed:", err);
            if (err instanceof Error) {
                if (err.message.includes('popup-closed-by-user')) {
                    console.warn("⚠️ [Login] Popup closed by user");
                } else {
                    setError('Failed to sign in. See console.');
                }
            } else {
                setError('Unknown error during sign in.');
            }
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="auth-logo">🌱</div>
                <h1>Idea Farm</h1>
                <p className="auth-subtitle">Capture and cultivate your ideas</p>

                {error && <div className="error-message">{error}</div>}

                {!needsDriveConsent ? (
                    <button
                        onClick={handleGoogleSignIn}
                        className="btn-google"
                        disabled={loading}
                    >
                        <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                        </svg>
                        {loading ? 'Signing in...' : 'Sign in with Google'}
                    </button>
                ) : (
                    <div className="consent-step">
                        <p className="consent-text">One last step! Please grant permission to save files to your Google Drive.</p>
                        <button
                            onClick={() => loginToDrive()}
                            className="btn-primary"
                            disabled={loading}
                        >
                            {loading ? 'Connecting...' : 'Connect Google Drive'}
                        </button>
                    </div>
                )}

                {!needsDriveConsent && <p className="auth-note">
                    We'll request access to Google Drive to store your idea content.
                </p>}
            </div>
        </div>
    );
}
