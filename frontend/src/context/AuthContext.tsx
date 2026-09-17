import { createContext, useEffect, useState, type ReactNode } from 'react';
import { authApi } from '../api/endpoints';
import type { User } from '../api/types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

// eslint-disable-next-line react-refresh/only-export-components -- context object is intentionally colocated with its provider
export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('darukaa_token');
    const cachedUser = localStorage.getItem('darukaa_user');
    if (token && cachedUser) {
      setUser(JSON.parse(cachedUser));
      // Verify token is still valid in the background.
      authApi
        .me()
        .then((freshUser) => {
          setUser(freshUser);
          localStorage.setItem('darukaa_user', JSON.stringify(freshUser));
        })
        .catch(() => {
          setUser(null);
        });
    }
    setLoading(false);
  }, []);

  const persistAuth = (token: string, freshUser: User) => {
    localStorage.setItem('darukaa_token', token);
    localStorage.setItem('darukaa_user', JSON.stringify(freshUser));
    setUser(freshUser);
  };

  const login = async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    persistAuth(res.access_token, res.user);
  };

  const register = async (name: string, email: string, password: string) => {
    const res = await authApi.register(name, email, password);
    persistAuth(res.access_token, res.user);
  };

  const logout = () => {
    localStorage.removeItem('darukaa_token');
    localStorage.removeItem('darukaa_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
