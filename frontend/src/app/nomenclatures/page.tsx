'use client'

import { useState } from "react";
import { Paper } from "@mui/material";
import './nomenclatures.scss'
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";
import TableComponent from "@/components/Ui/Table/Table";
import { useFetchNomenclatures, useGetVersions } from "@/hooks/useFetchNomenclatures";
import Search from "./components/Search/Search";
import { useDebounce } from "@/hooks/useDebounce";
import StatusSelect from "./components/Status/StatusSelect";
import TimezoneSelect from "./components/TimeZone/TimezoneSelect";
import { convertZone } from "@/types/timeZone";
import NomenclaturesService from "@/services/NomenclaturesService";
import VersionSelect from "./components/Version/VersionSelect";

const columns = [
    { id: "id", label: "ID", minWidth: 100 },
    { id: "name", label: "Название", minWidth: 170 },
    { id: "timezone", label: "Часовой пояс", minWidth: 170 },
    { id: "version", label: "Версия", minWidth: 170 },
    { id: "last_answer", label: "Последний ответ", minWidth: 120 },
    { id: "status", label: "Статус", minWidth: 120 },
];

export default function NomenclaturesPage() {
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(10);
    const [searchValue, setSearchValue] = useState<string>('');
    const [status, setStatus] = useState<string>('');
    const [zone, setZone] = useState<string>("");
    const [version, setVersion] = useState<string>('')
    const debouncedSearchValue = useDebounce(searchValue, 500);

    const { nomenclatures, isError, isLoading, error, totalItems } = useFetchNomenclatures(
        {
            page,
            limit,
            search: debouncedSearchValue,
            status: status,
            timezone: zone,
            version: version
        }
    );



    if (isError) console.error(error);

    const handleSearchChange = (event: { target: { value: string } }) => {
        setSearchValue(event.target.value);
    }

    const handleStatusChange = (status: string) => {
        setStatus(status);
    }

    const handleStatusTimezone = (zone: string) => {
        setZone(zone);
    }

    const handleVersionChange = (version: string) => {
        setVersion(version)
    }

    return (
        <Paper sx={{ width: "100%", overflow: "hidden" }}>
            <div style={{ display: 'flex', flexDirection: 'row', gap: '12px', alignItems: 'center', margin: '24px' }}>
                <Search
                    onSearchChange={handleSearchChange}
                    placeholder="Поиск"
                    searchValue={searchValue ? searchValue : ''}
                />
                <StatusSelect
                    status={status}
                    setStatus={handleStatusChange}
                />
                <TimezoneSelect
                    timezone={zone}
                    setTimezone={handleStatusTimezone}
                />
                <VersionSelect
                    setVersion={handleVersionChange}
                    version={version}
                />
            </div>
            <TableComponent
                data={nomenclatures}
                columns={columns}
                link="nomenclatures"
                limit={limit}
                loading={isLoading}
            />
            <CustomPagination
                totalItems={totalItems}
                itemsPerPage={limit}
                setItemsPerPage={setLimit}
                currentPage={page}
                setCurrentPage={setPage}
            />
        </Paper>
    );
}
