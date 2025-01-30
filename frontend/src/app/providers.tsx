"use client";

import { AuthProvider } from "@/providers/auth/AuthProvider";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AxiosError } from "axios";
import { ReactNode } from "react";

export interface ProvidersProps {
    children: ReactNode;
}

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: (failureCount, error) => {
                const axiosError = error as AxiosError;
                if (axiosError.response?.status === 401) {
                    alert(axiosError.response?.statusText || "Неавторизованный доступ");
                    window.location.href = "/login"
                    return false;
                }
                return failureCount < 3;
            },
        },
    },
});

function Providers({ children }: ProvidersProps) {
    return (
        <AuthProvider>
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        </AuthProvider>
    );
}

export default Providers;
