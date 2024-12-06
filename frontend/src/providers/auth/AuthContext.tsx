'use client';
import { IAuth } from '@/interfaces/Auth.interface';
import { createContext, useContext } from 'react';

interface AuthContextType {
    isAuthenticated: boolean; // Статус авторизации
    loading: boolean; // Статус загрузки
    login: ({ email, password }: IAuth) => Promise<void>; // Метод для входа
    logout: () => void; // Метод для выхода
}


export const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth должен использоваться внутри AuthProvider');
    }
    return context;
};
