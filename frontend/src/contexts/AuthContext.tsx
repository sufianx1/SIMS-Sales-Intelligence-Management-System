import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, CompanyMembership, LoginRequest } from '../types/auth';
import { authApi } from '../api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  activeCompany: CompanyMembership | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (creds: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  setActiveCompany: (company: CompanyMembership) => void;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('sms_auth_token'));
  const [activeCompany, setActiveCompanyState] = useState<CompanyMembership | null>(() => {
    const saved = localStorage.getItem('sms_active_company');
    return saved ? JSON.parse(saved) : null;
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('sms_auth_token');
      if (storedToken) {
        try {
          const profile = await authApi.getMe();
          setUser(profile);
          // Restore active company or select first available
          if (!activeCompany && profile.companies.length > 0) {
            const first = profile.companies[0];
            setActiveCompany(first);
          }
        } catch {
          logout();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const setActiveCompany = (company: CompanyMembership) => {
    setActiveCompanyState(company);
    localStorage.setItem('sms_active_company', JSON.stringify(company));
    localStorage.setItem('sms_active_company_id', company.company_id.toString());
  };

  const login = async (creds: LoginRequest) => {
    setIsLoading(true);
    try {
      const resp = await authApi.login(creds);
      setToken(resp.access_token);
      setUser(resp.user);
      localStorage.setItem('sms_auth_token', resp.access_token);

      if (resp.user.companies.length > 0) {
        setActiveCompany(resp.user.companies[0]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await authApi.logout();
      }
    } catch {
      // Ignore network errors on logout
    } finally {
      setToken(null);
      setUser(null);
      setActiveCompanyState(null);
      localStorage.removeItem('sms_auth_token');
      localStorage.removeItem('sms_active_company');
      localStorage.removeItem('sms_active_company_id');
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (user?.is_system_admin) return true;
    if (!activeCompany) return false;
    return activeCompany.permissions.includes(permission);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        activeCompany,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        logout,
        setActiveCompany,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
