import {Metadata} from "next";
import NomenclaturesPage from "./NomenclaturesClientPage";
import ApiRequest from "@/services/ApiRequest";
import {INomenclaturesResponse, INomenclaturesService} from "@/interfaces/Nomenclatures.interface";
import NomenclaturesService from "@/services/NomenclaturesService";
import {getFiles} from "@/app/files/page";
import {cookies} from "next/headers";

export const metadata: Metadata = {
    title: "Номенклатуры",
    description: "Список номенклатур",
};

export async function getNomenclatures(queryParams: Record<string, string>): Promise<INomenclaturesResponse> {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("accessToken")?.value;
    const queryString = new URLSearchParams(queryParams).toString();
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/nomenclatures?${queryString}`;

    const res = await fetch(url, {
        cache: "no-store",
        headers: {
            Authorization: `access_token ${accessToken}`,
        }
    });

    if (!res.ok) throw new Error("Ошибка загрузки файлов");
    return res.json();
}


export default async function Page({searchParams}: { searchParams?: Record<string, string> }) {

    if (!searchParams) {
        throw new Error("no searchParams provided");
    }

    const params = new URLSearchParams(Object.entries(searchParams ?? {}));
    const page = params.get("page") ?? "1";
    const limit = params.get("limit") ?? "100";

    const nomenclatures = await getNomenclatures({page, limit});
    console.log(nomenclatures)
    return (
        <NomenclaturesPage initialData={nomenclatures.results}/>
    )
}
