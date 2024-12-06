"use client";

import { AuthProvider } from "@/providers/auth/AuthProvider";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
// import { useRouter } from "next/navigation";

export interface ProvidersProps {
    children: React.ReactNode;
}

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
        },
    },
});

export function Providers({ children }: ProvidersProps) {
    //   const router = useRouter();

    return (
        <AuthProvider>
            <QueryClientProvider client={queryClient}>
                {/* <ReduxProvider store={store}> */}
                {/* <ReduxToastrProvider /> */}
                {children}
                {/* </ReduxProvider> */}
            </QueryClientProvider>
        </AuthProvider>
    );
}
