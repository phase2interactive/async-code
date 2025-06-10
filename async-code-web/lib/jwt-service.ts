import { SignJWT, jwtVerify } from 'jose';

const JWT_KEY = 'jwt_tokens';
const JWT_REFRESH_KEY = 'jwt_refresh_token';

interface JWTTokens {
    access_token: string;
    refresh_token: string;
    expires_in: number;
}

interface TokenPayload {
    user_id: string;
    type: 'access' | 'refresh';
    exp: number;
    iat: number;
}

class JWTService {
    /**
     * Store JWT tokens in localStorage
     */
    storeTokens(tokens: JWTTokens): void {
        const expiresAt = Date.now() + (tokens.expires_in * 1000);
        
        localStorage.setItem(JWT_KEY, JSON.stringify({
            access_token: tokens.access_token,
            expires_at: expiresAt
        }));
        
        localStorage.setItem(JWT_REFRESH_KEY, tokens.refresh_token);
    }

    /**
     * Get access token from storage
     */
    getAccessToken(): string | null {
        const stored = localStorage.getItem(JWT_KEY);
        if (!stored) return null;
        
        try {
            const data = JSON.parse(stored);
            
            // Check if token is expired
            if (Date.now() >= data.expires_at) {
                this.clearTokens();
                return null;
            }
            
            return data.access_token;
        } catch {
            return null;
        }
    }

    /**
     * Get refresh token from storage
     */
    getRefreshToken(): string | null {
        return localStorage.getItem(JWT_REFRESH_KEY);
    }

    /**
     * Clear all tokens from storage
     */
    clearTokens(): void {
        localStorage.removeItem(JWT_KEY);
        localStorage.removeItem(JWT_REFRESH_KEY);
    }

    /**
     * Check if access token is expired or about to expire
     */
    isAccessTokenExpired(): boolean {
        const stored = localStorage.getItem(JWT_KEY);
        if (!stored) return true;
        
        try {
            const data = JSON.parse(stored);
            // Consider token expired if less than 5 minutes remaining
            return Date.now() >= (data.expires_at - 5 * 60 * 1000);
        } catch {
            return true;
        }
    }

    /**
     * Decode JWT token (client-side, no verification)
     */
    decodeToken(token: string): TokenPayload | null {
        try {
            const parts = token.split('.');
            if (parts.length !== 3) return null;
            
            const payload = JSON.parse(atob(parts[1]));
            return payload;
        } catch {
            return null;
        }
    }

    /**
     * Get user ID from stored access token
     */
    getUserId(): string | null {
        const token = this.getAccessToken();
        if (!token) return null;
        
        const payload = this.decodeToken(token);
        return payload?.user_id || null;
    }
}

export const jwtService = new JWTService();