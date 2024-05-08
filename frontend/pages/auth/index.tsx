// pages/login.tsx

import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { AuthService } from '@/services/auth/auth.service';

export default function LoginPage() {
    const [email, setEmail] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [error, setError] = useState<string>('');
    const router = useRouter();

    const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        try {
            const response = await AuthService.login(email, password);
            if (response.status === 200) {
                router.push('/');
            } else {
                throw new Error('Не удалось выполнить вход');
            }
        } catch (error: Error | any) {
            setError(error.response?.data?.message || 'Ошибка при входе');
        }
    };

    const logOut = () => {
        AuthService.logout();
    }

    return (
        <div>
            <form onSubmit={handleLogin}>
                <h1>Вход</h1>
                <div>
                    <label>Email</label>
                    <input value={email} onChange={(e) => setEmail(e.target.value)} />
                </div>
                <div>
                    <label>Пароль</label>
                    <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                </div>
                <button type="submit">Войти</button>
                {error && <p>{error}</p>}
            </form>
            <button onClick={logOut}>Exit</button>
        </div>
    );
}
