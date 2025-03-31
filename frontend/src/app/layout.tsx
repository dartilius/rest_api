'use client'

import localFont from 'next/font/local'
import '../styles/globals.scss'
import AdminLayout from './login/layout'
import { usePathname } from 'next/navigation'
import { ReactNode, useState } from 'react'
import Sidebar from '@/components/Ui/Sidebar/Sidebar'
import Providers from './providers'
import Head from 'next/head'
import Navbar from '@/components/Ui/navbar/Navbar'

const fonts = localFont({
  src: [
    {
      path: '../styles/fonts/montserrat/Montserrat-Light.ttf',
      style: 'inherit',
      weight: '300',
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Medium.ttf',
      style: 'inherit',
      weight: '500',
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Regular.ttf',
      style: 'inherit',
      weight: '400',
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-SemiBold.ttf',
      style: 'inherit',
      weight: '600',
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Bold.ttf',
      style: 'inherit',
      weight: '700',
    },
    {
      path: '../styles/fonts/montserrat/Montserrat-Black.ttf',
      style: 'inherit',
      weight: '900',
    },
  ],
})

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode
}>) {
  const [openSideBar, setOpenSideBar] = useState<boolean>(true)
  const [isAnimating, setIsAnimating] = useState<boolean>(false)

  const pathname = usePathname()
  const isLoginPage = pathname === '/login'

  const toggleSidebar = () => {
    if (isAnimating) return // Блокируем повторное нажатие во время анимации
    setIsAnimating(true)
    setOpenSideBar((prev) => !prev)

    // Устанавливаем таймер завершения анимации (300ms как в SCSS)
    setTimeout(() => setIsAnimating(false), 300)
  }
  return (
    <html lang='en'>
      <Head>
        <title>RMC</title>
        <meta name='description' content='Реклама в ТЦ' />
        <meta name='viewport' content='width=device-width, initial-scale=1.0' />
        <link rel='icon' href='/favicon.ico' type='image/ico' />
      </Head>
      <body className={`${fonts.className} antialiased`}>
        <Providers>
          {isLoginPage ? (
            <AdminLayout>{children}</AdminLayout>
          ) : (
            <div className='layout'>
              <Navbar toggleSidebar={toggleSidebar} />
              <div className='flex_sidebar_and_main'>
                <Sidebar isOpen={openSideBar}/>
                <main className='content'>
                  {children}
                </main>
              </div>
            </div>
          )}
        </Providers>
      </body>
    </html>
  )
}
