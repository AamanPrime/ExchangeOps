import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';

interface User {
    id: number;
    username: string;
    role: 'quant' | 'infra' | 'compliance' | 'ops' | 'admin';
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (token: string) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        if (token) {
            try {
                // In a real app, the role might be a custom claim in the JWT.
                // For this demo, we'll pretend we extract it, or we fetch it from a /me endpoint.
                // Assuming simple JWT and we decode the token. Let's mock the role extraction.
                // We'll map standard username to roles for demo purposes.
                const decoded: any = jwtDecode(token);
                
                let role: User['role'] = 'admin'; // fallback
                // We will rely on username matching role for the seed data
                if (decoded.username) {
                    const uname = decoded.username.toLowerCase();
                    if (uname.includes('quant')) role = 'quant';
                    else if (uname.includes('infra')) role = 'infra';
                    else if (uname.includes('compliance')) role = 'compliance';
                    else if (uname.includes('ops')) role = 'ops';
                }

                setUser({
                    id: decoded.user_id,
                    username: decoded.username || 'User',
                    role: role,
                });
            } catch (e) {
                console.error("Invalid token");
                logout();
            }
        }
    }, [token]);

    const login = (newToken: string) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};
