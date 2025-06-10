'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { getSupabase } from '@/lib/supabase'
import { ApiService } from '@/lib/api-service'
import { jwtService } from '@/lib/jwt-service'

interface AuthContextType {
    user: User | null
    session: Session | null
    loading: boolean
    signOut: () => Promise<void>
    isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}

interface AuthProviderProps {
    children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null)
    const [session, setSession] = useState<Session | null>(null)
    const [loading, setLoading] = useState(true)
    const [isAuthenticated, setIsAuthenticated] = useState(false)

    // Function to handle JWT token generation
    const handleAuthentication = async (session: Session | null) => {
        if (session?.user) {
            try {
                // Generate JWT tokens
                const tokens = await ApiService.generateToken(session.user.id)
                jwtService.storeTokens(tokens)
                setIsAuthenticated(true)
            } catch (error) {
                console.error('Failed to generate JWT tokens:', error)
                setIsAuthenticated(false)
            }
        } else {
            jwtService.clearTokens()
            setIsAuthenticated(false)
        }
    }

    // Function to refresh token if needed
    const refreshTokenIfNeeded = async () => {
        if (jwtService.isAccessTokenExpired()) {
            const refreshToken = jwtService.getRefreshToken()
            if (refreshToken) {
                try {
                    const result = await ApiService.refreshToken(refreshToken)
                    jwtService.storeTokens({
                        access_token: result.access_token,
                        refresh_token: refreshToken,
                        expires_in: result.expires_in
                    })
                } catch (error) {
                    console.error('Failed to refresh token:', error)
                    // If refresh fails, clear tokens and re-authenticate
                    jwtService.clearTokens()
                    if (session) {
                        await handleAuthentication(session)
                    }
                }
            }
        }
    }

    useEffect(() => {
        const supabase = getSupabase()
        
        // Get initial session
        supabase.auth.getSession().then(async ({ data: { session } }) => {
            setSession(session)
            setUser(session?.user ?? null)
            await handleAuthentication(session)
            setLoading(false)
        })

        // Listen for auth changes
        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange(async (event, session) => {
            setSession(session)
            setUser(session?.user ?? null)
            await handleAuthentication(session)
            setLoading(false)
        })

        // Set up token refresh interval
        const tokenRefreshInterval = setInterval(() => {
            refreshTokenIfNeeded()
        }, 60000) // Check every minute

        return () => {
            subscription.unsubscribe()
            clearInterval(tokenRefreshInterval)
        }
    }, [])

    const signOut = async () => {
        const supabase = getSupabase()
        await supabase.auth.signOut()
        jwtService.clearTokens()
        setIsAuthenticated(false)
    }

    const value = {
        user,
        session,
        loading,
        signOut,
        isAuthenticated,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
} 