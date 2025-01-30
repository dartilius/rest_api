'use client';

import { AuthContext } from '@/providers/auth/AuthContext';
import { Button } from '@mui/material';
import { useRouter } from 'next/navigation';
import { useContext } from 'react';

const AuthButton = () => {
    const contextAuth = useContext(AuthContext);
    const router = useRouter();

    if (!contextAuth) throw new Error('Проблема авторизации')

    const handleLogout = () => {
        contextAuth.logout();
        router.push('/'); // Возвращаем пользователя на главную страницу
    };;

    const handleLoginRedirect = () => {
        router.push('/login'); // Перенаправляем на страницу авторизации
    };

    // console.log('contextAuth.isAuthenticated', contextAuth.isAuthenticated);

    return (
        <Button
            color={contextAuth.isAuthenticated ? "error" : "primary"}
            onClick={contextAuth.isAuthenticated ? handleLogout : handleLoginRedirect}
        >
            {contextAuth.isAuthenticated ? 'Выйти' : 'Войти'}
        </Button>
    );
};

export default AuthButton;
