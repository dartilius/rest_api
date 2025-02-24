import TableNomenclatures from "@/app/nomenclatures/components/Table/TableNomenclatures";
import {FiltersModalWrapper} from "@/app/nomenclatures/components/FiltersModalWrapper";

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
    const openModalFilters = String(searchParams?.openModalFilters) === 'true';

    return (
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <FiltersModalWrapper openModalFilters={openModalFilters} />
            <TableNomenclatures name={name} currentPage={currentPage} limit={limit} version={version} status={status} timezone={timezone} />
        </div>
    );
}