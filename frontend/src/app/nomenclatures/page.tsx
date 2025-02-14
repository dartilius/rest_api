import {Metadata} from "next";
import NomenclaturesPage from "./NomenclaturesClientPage";
import ApiRequest from "@/services/ApiRequest";
import {INomenclaturesResponse, INomenclaturesService} from "@/interfaces/Nomenclatures.interface";
import NomenclaturesService from "@/services/NomenclaturesService";
import {getFiles} from "@/app/files/page";
import FiltersModal from "@/app/nomenclatures/components/FiltersModal";
import {getClientAccessToken, getServerAccessToken} from "@/utils";

// export const metadata: Metadata = {
//     title: "Номенклатуры",
//     description: "Список номенклатур",
// };
const isSSR = typeof window === "undefined";
console.log('isSsr', isSSR)
export async function getNomenclatures(queryParams: {
    page: number;
    limit: number;
    name: string;
    status: string;
    timezone: string;
    version: string;
}): Promise<INomenclaturesResponse> {
    let token
    if (isSSR) {
        // Для SSR получаем токен с сервера
        token = await getServerAccessToken();
        console.log('token isSsr', token);
    } else {
        // Для клиента получаем токен с клиента
        token = getClientAccessToken();
        console.log('token !isSsr', token);
    }
    // Convert page and limit to strings
    const stringifiedQueryParams = {
        ...queryParams,
        page: queryParams.page.toString(),
        limit: queryParams.limit.toString()
    };

    const queryString = new URLSearchParams(stringifiedQueryParams).toString();
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/nomenclatures?${queryString}`;

    const res = await fetch(url, {
        cache: "no-store",
        headers: {
            Authorization: `access_token ${token}`,
        }
    });

    if (!res.ok) throw new Error("Ошибка загрузки файлов");
    return res.json();
}


export default async function Page({ searchParams }: { searchParams?: {
        page: number;
        limit: number;
        name: string;
        status: string;
        timezone: string;
        version: string
    } }) {
    // Wait for searchParams to be available
    const { page = 1, limit = 10, name = "", status = "", timezone = "", version = "" } = await searchParams ?? {};

    const nomenclatures = await getNomenclatures({ page, limit, name, status, timezone, version });
    console.log(nomenclatures);

    return (
        <NomenclaturesPage initialData={nomenclatures.results} />
    );
}
