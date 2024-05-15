import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { Layout } from "antd/lib";
import LayoutAdmin from "@/components/myUi/LayoutAmin";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <LayoutAdmin>
        <Component {...pageProps} />
    </LayoutAdmin>
  )
}