'use client'
import { Inter } from "next/font/google";
import "./globals.css";
import { Layout, Menu, theme } from 'antd/lib';
import Link from "next/link";
import { links } from "@/shared/types/links";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AuthService } from "@/services/auth/auth.service";

const { Header, Footer, Content } = Layout;
const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const pathname = usePathname();
  const router = useRouter();
  const [selectedKey, setSelectedKey] = useState('1');

  useEffect(() => {
    const currentItem = links.find(link => link.link === pathname);
    if (currentItem) {
      setSelectedKey(currentItem.key);
    }
  }, [pathname]);

  if (pathname === '/login') {
    return <>{children}</>
  }

  const logOut = () => {
    AuthService.logout();
    router.push('/login');
  }


  return (
    <html lang="ru">
      <body>
        <Layout className={inter.className} style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <Header>
            <Menu
              theme="dark"
              mode="horizontal"
              selectedKeys={[selectedKey]}
              style={{ flex: 1, minWidth: 0 }}
            >
              {links.map(item => (
                <Menu.Item key={item.key}>
                  <Link href={item.link}>{item.label}</Link>
                </Menu.Item>
              ))}
              <Menu.Item onClick={logOut} key="9">
                Выход
              </Menu.Item>
            </Menu>
          </Header>
          <Content style={{
            background: colorBgContainer,
            flex: 1,
            padding: 24,
            borderRadius: borderRadiusLG,
          }}>
            {children}
          </Content>
          <Footer style={{ textAlign: 'center' }}>
            Ant Design ©{new Date().getFullYear()} Created by Ant UED
          </Footer>
        </Layout>
      </body>
    </html>
  );
}
