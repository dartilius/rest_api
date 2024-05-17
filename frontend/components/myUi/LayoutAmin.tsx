import LoginPage from "@/pages/login";
import { Layout, Menu } from "antd/lib";
import { useRouter } from "next/router";
import LoginPage from "@/pages/login";

const { Header, Content, Footer } = Layout;


export default function LayoutAdmin({children}: any) {

    const router = useRouter();
    const pathName = router.pathname;

    if (pathName === '/auth') {
        return <LoginPage />
    }

    return (
        <div>
            <Layout>
                <Header>
                    <Menu
                        theme="light"
                        mode="horizontal"
                    />
                </Header>
                <Content>
                    {children}
                </Content>
                {/* <Footer>
                    vdlmksfslkfjskl
                </Footer> */}
            </Layout>
        </div>
    );
}