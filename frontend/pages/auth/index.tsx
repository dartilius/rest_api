// pages/login.tsx

import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { AuthService } from '@/services/auth/auth.service';
import styles from './Auth.module.scss'

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
                router.push('/nomenclatures');
            } else {
                throw new Error('Не удалось выполнить вход');
            }
        } catch (error: Error | any) {
            setError(error.response?.data?.message || 'Ошибка при входе');
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.container_left}>
            </div>
            <div className={styles.container_right}>
                <form onSubmit={handleLogin} className={styles.container_right_login}>
                    <h1 className={styles.container_right_login_title}>Вход</h1>
                    <div className={styles.container_right_login_email}>
                        <label className={styles.container_right_login_email_label}>Email</label>
                        <input className={styles.container_right_login_email_input} value={email} onChange={(e) => setEmail(e.target.value)} />
                    </div>
                    <div className={styles.container_right_login_password}>
                        <label className={styles.container_right_login_password_label}>Пароль</label>
                        <input className={styles.container_right_login_password_input} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                    </div>
                    <button type="submit" className={styles.container_right_login_button}>
                        <p className={styles.container_right_login_button_text}>Войти</p>
                    </button>
                    {error && <p>{error}</p>}
                </form>
            </div>
        </div>
    );
}
