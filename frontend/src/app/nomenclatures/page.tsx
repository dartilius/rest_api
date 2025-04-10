import {FiltersWrapper, TableNomenclatures} from "@/app/nomenclatures/components";
import {Metadata} from "next";
import {getNomenclaturesList, nomenclaturesService} from "@/app/nomenclatures/api";

export const metadata: Metadata = {
    title: 'Номенклатуры',
    description: 'Страница со списком номенклатур',
    icons: {
        icon: '/favicon.svg'
    }
}

type NomenclaturesListProps = {
    page?: number | string;
    limit?: number | string;
    name?: string;
    status?: string;
    timezone?: string;
    version?: string;
    openModalFilters?: boolean;
}


export default async function Page(props: {
    searchParams?: Promise<NomenclaturesListProps>
}) {

    const searchParams = await props.searchParams
    const name = searchParams?.name || '';
    const currentPage = Number(searchParams?.page) || 1;
    const limit = Number(searchParams?.limit) || 10;
    const version = searchParams?.version || '';
    const status = searchParams?.status || '';
    const timezone = searchParams?.timezone || '';

    const listNomenclature = await getNomenclaturesList({
        searchParams: Promise.resolve({
            page: currentPage,
            limit: limit,
            name,
            status,
            timezone,
            version
        })
    })

    return (
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <FiltersWrapper />
            <TableNomenclatures count={listNomenclature.count} data={listNomenclature.results} />
        </div>
    );
}