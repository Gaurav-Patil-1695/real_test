import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { login as apiLogin, register as apiRegister, logout as apiLogout, me as apiMe, refresh as apiRefresh } from '../api/auth';
import { getAccessToken, setAccessToken, clearTokens } from './tokenStore';
import type { User, LoginRequest, RegisterRequest } from '../api/types';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refresh = useCallback(async () => {
    try {
      const response = await apiRefresh();
      setAccessToken(response.accessToken);
      const currentUser = await apiMe();
      setUser(currentUser);
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      const token = getAccessToken();
      if (token) {
        try {
          const currentUser = await apiMe();
          setUser(currentUser);
        } catch {
          try {
            await refresh();
          } catch {
            clearTokens();
            setUser(null);
          }
        }
      } else {
        try {
          await refresh();
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [refresh]);

  const login = useCallback(async (data: LoginRequest) => {
    const response = await apiLogin(data);
    setAccessToken(response.accessToken);
    const currentUser = await apiMe();
    setUser(currentUser);
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    const response = await apiRegister(data);
    setAccessToken(response.accessToken);
    const currentUser = await apiMe();
    setUser(currentUser);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      register,
      logout,
      refresh,
    }),
    [user, isLoading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
