'use client'
import { useAuth } from "@/src/providers/auth/AuthContext";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function LoginPage() {

  const { login } = useAuth()
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const route = useRouter()

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await login({ email, password }).then(() => {
      route.push('/home')
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        placeholder="Пароль"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button type="submit">Войти</button>
    </form>
  );
}