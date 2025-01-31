'use client'

import { useState } from "react";
import { Box, Paper } from "@mui/material";
import './nomenclatures.scss'
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";
import TableComponent from "@/components/Ui/Table/Table";
import { useFetchNomenclatures } from "@/hooks/useFetchNomenclatures";
import Search from "./components/Search/Search";
import { useDebounce } from "@/hooks/useDebounce";
import StatusSelect from "./components/Status/StatusSelect";
import TimezoneSelect from "./components/TimeZone/TimezoneSelect";
import VersionSelect from "./components/Version/VersionSelect";

const columns = [
    { id: "name", label: "Название", minWidth: 170 },
    { id: "timezone", label: "Часовой пояс", maxWidth: 170 },
    { id: "version", label: "Версия", maxWidth: 170 },
    { id: "last_answer", label: "Последний ответ", minWidth: 120 },
    {
        id: "status",
        label: "Статус",
        minWidth: 120,
        renderCell: (row: any) => (
            <Box
                sx={{
                    display: "inline-block",
                    padding: "4px 8px",
                    borderRadius: "8px",
                    backgroundColor: getStatusColor(row.status),
                    color: "white",
                    textAlign: "center",
                    minWidth: "80px",
                }}
            >
                {row.status}
            </Box>
        ),
    },
];

// Функция для определения цвета статуса
function getStatusColor(statusId: number): string {
    switch (statusId) {
        case 0: return "#4caf50"; // Зеленый для онлайн
        case 1: return "#ff9800"; // Оранжевый для оффлайн 5 минут
        case 2: return "#f44336"; // Красный для оффлайн час
        default: return "#9e9e9e"; // Серый для неизвестного статуса
    }
}


export default function NomenclaturesPage() {
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(10);
    const [searchValue, setSearchValue] = useState<string>("");
    const [status, setStatus] = useState<string>("");
    const [zone, setZone] = useState<string>("");
    const [version, setVersion] = useState<string>("");
    const debouncedSearchValue = useDebounce(searchValue, 500);

    const { nomenclatures, isError, isLoading, error, totalItems } = useFetchNomenclatures({
        page,
        limit,
        search: debouncedSearchValue,
        status: status,
        timezone: zone,
        version: version,
    });

    if (isError) console.error(error);

    const handleSearchChange = (event: { target: { value: string } }) => {
        setSearchValue(event.target.value);
    };

    const handleStatusChange = (status: string) => {
        setStatus(status);
    };

    const handleStatusTimezone = (zone: string) => {
        setZone(zone);
    };

    const handleVersionChange = (version: string) => {
        setVersion(version);
    };

    return (
        <Paper sx={{ width: "100%", overflow: "hidden" }}>
            <div
                style={{
                    display: "flex",
                    flexDirection: "row",
                    gap: "12px",
                    alignItems: "center",
                    margin: "24px",
                }}
            >
                <Search
                    onSearchChange={handleSearchChange}
                    placeholder="Поиск"
                    searchValue={searchValue ? searchValue : ""}
                />
                <StatusSelect status={status} setStatus={handleStatusChange} />
                <TimezoneSelect timezone={zone} setTimezone={handleStatusTimezone} />
                <VersionSelect setVersion={handleVersionChange} version={version} />
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