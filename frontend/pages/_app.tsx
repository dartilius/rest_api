import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { Layout } from "antd/lib";
import { middleware } from "./_middleware";

export default function App({ Component, pageProps }: AppProps) {
  return (
    // <Layout>
    //   <Header />
      <Component {...pageProps} />
    //   <Footer />
    // </Layout>
  )
}