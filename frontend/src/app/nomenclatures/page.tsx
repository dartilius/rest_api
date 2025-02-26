import {FiltersWrapper, TableNomenclatures} from "@/app/nomenclatures/components";
import {Suspense} from "react";


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

    return (
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <FiltersWrapper />
            <TableNomenclatures name={name} currentPage={currentPage} limit={limit} version={version} status={status} timezone={timezone} />
        </div>
    );
}