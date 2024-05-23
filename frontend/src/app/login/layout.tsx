'use client'
import { Layout, theme } from 'antd/lib';

const { Header, Footer, Content } = Layout;

export default function LoginLayout({children}: {children: React.ReactNode}) {

    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();

    return (
        <html lang="ru">
            <body>
                <Layout style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
                    <Header />
                    <Content style={{
                        background: colorBgContainer,
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