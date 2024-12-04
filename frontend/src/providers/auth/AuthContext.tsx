'use client';

import { IAuthInput } from '@/src/types/interface/user.interface';
import { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
    isAuthenticated: boolean; // Статус авторизации
    loading: boolean; // Статус загрузки
    login: ({ email, password }: IAuthInput) => Promise<void>; // Метод для входа
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
