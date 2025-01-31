import { API_URL } from "@/config/api.config";
import { Metadata } from "next";
import NomenclaturesPage from "./NomenclaturesClientPage";
import { cookies } from "next/headers";

export const metadata: Metadata = {
    title: "Номенклатуры",
    description: "Список номенклатур",
};

async function getData() {
    try {

        const accessToken = (await cookies()).get("accessToken")?.value;
        const url = new URL(`${API_URL}nomenclatures/`);

        const res = await fetch(url.toString(), {
            cache: "no-store",
            headers: {
                Authorization: `access_token ${accessToken}`,
            },
        });

        if (!res.ok) {
            throw new Error(`Ошибка загрузки данных: ${res.statusText}`);
        }

        const data = await res.json();
        return data;

    } catch (error: unknown) {
        if (error instanceof Error) {
            console.error("Ошибка:", error.message);
        } else {
            console.error("Неизвестная ошибка", error);
        }
    }
}

export default async function Page() {
    try {
        const data = await getData();
        console.log('Data:', data);

        return <NomenclaturesPage />;
    } catch (error) {
        if (error instanceof Error) {
            console.error("error:", error.message);

            return <div>Произошла ошибка: {error.message}</div>;
        } else {
            return (
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                        gap: "12px",
                        alignItems: "center",
                    }}
                >
                    Произошла непредвиденная ошибка. Пожалуйста обновите страницу, или повторите попытку позже.
                    <div style={{ fontSize: "24px" }}>😔</div>
                </div>
            );
        }
    }
}
