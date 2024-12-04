'use client'
import { useAuth } from "@/src/providers/auth/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LogoutPage() {
    const { logout } = useAuth();
    const router = useRouter();

    useEffect(() => {
        const performLogout = async () => {
            await logout(); // Выполняем логаут
            router.push("/login"); // Перенаправляем на страницу логина
        };

        performLogout();
    }, [logout, router]);

    return <div>Выход из системы...</div>;
}