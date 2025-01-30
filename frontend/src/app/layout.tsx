'use client'

import localFont from "next/font/local";
import "../styles/globals.scss";
import Link from "next/link";
import AdminLayout from "./login/layout";
import { usePathname } from "next/navigation";
import { ReactNode, useState } from "react";
import burgerMenu from '@/styles/img/Navigation/Icon.svg'
import Image from "next/image";
import AuthButton from "@/components/AuthButton/AuthButton";
import Sidebar from "@/components/Ui/Sidebar/Sidebar";
import Providers from "./providers";

const fonts = localFont({
  src: [
    {
      path: '../styles/fonts/montserrat/Montserrat-Light.ttf',
      style: 'inherit',
      weight: '300'
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Medium.ttf',
      style: 'inherit',
      weight: '500'
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Regular.ttf',
      style: 'inherit',
      weight: '400'
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-SemiBold.ttf',
      style: 'inherit',
      weight: '600'
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Bold.ttf',
      style: 'inherit',
      weight: '700'
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Black.ttf',
      style: 'inherit',
      weight: '900'
    },
  ],
})

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const [openSideBar, setOpenSideBar] = useState<boolean>(true);
  const [isAnimating, setIsAnimating] = useState<boolean>(false);

  const pathname = usePathname()

  const isLoginPage = pathname === "/login";

  const toggleSidebar = () => {
    if (isAnimating) return; // Блокируем повторное нажатие во время анимации
    setIsAnimating(true);
    setOpenSideBar((prev) => !prev);

    // Устанавливаем таймер завершения анимации (300ms как в SCSS)
    setTimeout(() => setIsAnimating(false), 300);
  };
  return (
    <html lang="en">
      <body className={`${fonts.className} antialiased`}>
        <Providers>
          {isLoginPage ? (
            <AdminLayout>{children}</AdminLayout>
          ) : (
            <div className="layout">
              <aside
                className={`sidebar ${openSideBar ? "open" : "closed"
                  } ${isAnimating ? "animating" : ""}`}
              >
                <div className="sidebar__title">
                  <Link href={"/home"}>RMC ADMIN</Link>
                </div>
                <Sidebar />
              </aside>
              <div className="main">
                <header
                  className={`header ${!openSideBar ? "full-width" : ""}`}
                >
                  <div
                    className="header__toggle"
                    onClick={toggleSidebar}
                  >
                    <Image src={burgerMenu} alt="burgerMenu" width={24} height={24} />
                  </div>
                  <AuthButton />
                </header>
                <main className="content">{children}</main>
              </div>
            </div>
          )}
        </Providers>
      </body>
    </html>
  );
}
