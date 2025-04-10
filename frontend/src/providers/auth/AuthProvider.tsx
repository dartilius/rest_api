'use client';

import React, { useState, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import AuthService from '@/services/AuthService';
import { IAuth } from '@/interfaces/Auth.interface';
import {deleteCookie, setCookie} from 'cookies-next';

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    const fetchUser = async () => {
        const accessToken = localStorage.getItem('accessToken');
        if (!accessToken) return setIsAuthenticated(false);

        try {
            await AuthService.accessCreate({ access: accessToken }); // Проверяем токен
            setIsAuthenticated(true);
        } catch {
            localStorage.removeItem('accessToken'); // Удаляем невалидный токен
            deleteCookie('accessToken');
        } finally {
            setLoading(false);
        }
    };

    const login = async ({ email, password }: IAuth) => {
        setLoading(true);
        try {
            const { data } = await AuthService.login({ email, password });
            setCookie('accessToken', data.access)
            setCookie('refreshToken', data.refresh)
            localStorage.setItem('accessToken', data.access);
            localStorage.setItem('refreshToken', data.refresh);
            setIsAuthenticated(true);
        } catch (error) {
            console.error('Ошибка при входе:', error);
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        setIsAuthenticated(false);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        deleteCookie('accessToken');
        deleteCookie('refreshToken');
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
