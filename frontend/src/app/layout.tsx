import "../styles/globals.scss";
import { Metadata, Viewport } from "next";
import { Link } from "@nextui-org/link";
import clsx from "clsx";

import { Providers } from "./providers";
import { fontSans } from "@/src/config/fonts";
import { Navbar } from "@/src/components/navbar";
import {ReactNode} from "react";

export const metadata: Metadata = {
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "black" },
  ],
};

export default function RootLayout({ children,}: {children: ReactNode;}) {
    return (
        <html suppressHydrationWarning lang="en">
        <head/>
        <body
            className={clsx(
                "min-h-screen bg-background font-sans antialiased",
                fontSans.variable
            )}
        >
        <Providers themeProps={{attribute: "class", defaultTheme: "dark"}}>
            <div className="relative flex flex-col items-center h-screen">
                <Navbar/>
                <main className="w-full max-w-6xl px-4 flex-grow">
                    {children}
                </main>
                <footer className="w-full max-w-xl flex items-center justify-center py-3">
                    <Link
                        isExternal
                        className="flex items-center gap-1 text-current"
                        href="https://nextui-docs-v2.vercel.app?utm_source=next-app-template"
                        title="nextui.org homepage"
                    >
                        <span className="text-default-600">Powered by</span>
                        <p className="text-primary">NextUI</p>
                    </Link>
                </footer>
            </div>
        </Providers>
        </body>
        </html>
    );
}

