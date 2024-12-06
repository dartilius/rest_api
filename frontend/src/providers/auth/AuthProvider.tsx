'use client';

import React, { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import AuthService from '@/services/AuthService';
import { IAuth } from '@/interfaces/Auth.interface';

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    const fetchUser = async () => {
        const accessToken = localStorage.getItem('accessToken');
        if (!accessToken) {
            setIsAuthenticated(false);
            setLoading(false);
            return;
        }

        try {
            await AuthService.accessCreate({ access: accessToken }); // Проверяем токен
            setIsAuthenticated(true);
        } catch (error) {
            console.error('Токен недействителен или истек:', error);
            setIsAuthenticated(false);
            localStorage.removeItem('accessToken'); // Удаляем невалидный токен
        } finally {
            setLoading(false);
        }
    };

    const login = async ({ email, password }: IAuth) => {
        try {
            setLoading(true);
            const { data } = await AuthService.login({ email, password });
            localStorage.setItem('accessToken', data.access);
            localStorage.setItem('refreshToken', data.refresh);
            setIsAuthenticated(true);
        } catch (error) {
            console.error('Ошибка при входе:', error);
            setIsAuthenticated(false);
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setIsAuthenticated(false);
    };

    useEffect(() => {
        fetchUser(); // Проверяем пользователя при загрузке
    }, []);

    return (
        <AuthContext.Provider value={{ isAuthenticated, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
