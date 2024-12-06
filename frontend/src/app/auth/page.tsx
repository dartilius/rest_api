'use client';
import { useAuth } from "@/providers/auth/AuthContext";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import './auth.scss'
import logo from '../../../public/logo.jpg'

export default function LoginPage() {
    const { login } = useAuth();
    const [email, setEmail] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [error, setError] = useState<string | null>(null); // Для отображения ошибок
    const router = useRouter();

    const handleSubmit = async (event: FormEvent) => {
        event.preventDefault();
        try {
            await login({ email, password });
            router.push('/home');
        } catch (err: any) {
            setError(err.message || 'Ошибка авторизации'); // Обработка ошибки
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-container">
                <div className="logo">
                    <Image src={logo} alt="Логотип" width={640} height={480} />
                </div>
                <h1 className="title">Вход в систему</h1>
                {error && <div className="error">{error}</div>}
                <form onSubmit={handleSubmit} className="form">
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="input-field"
                        required
                    />
                    <input
                        type="password"
                        placeholder="Пароль"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="input-field"
                        required
                    />
                    <button type="submit" className="login-btn">Войти</button>
                </form>
                <div className="forgot-password">Забыли пароль?</div>
            </div>
            <div className="footer">© 2024 АРЭМСИ24. Все права защищены.</div>
        </div>
    );
}
