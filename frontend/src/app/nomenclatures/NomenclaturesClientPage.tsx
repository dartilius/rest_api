'use client'

import { useEffect, useState } from "react";
import { Box, Button, Paper } from "@mui/material";
import './nomenclatures.scss'
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";
import TableComponent from "@/components/Ui/Table/Table";
import { useFetchNomenclatures } from "@/hooks/useFetchNomenclatures";
import { useDebounce } from "@/hooks/useDebounce";
import FiltersModal from "./components/FiltersModal";

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

    const [isFiltersModalOpen, setFiltersModalOpen] = useState(false);

    const handleSearchChange = (searchValue: string) => {
        setSearchValue(searchValue);
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

    useEffect(() => {
        setPage(1)
    }, [status, version, searchValue, zone])

    return (
        <Paper sx={{ width: "100%", overflow: "hidden" }}>
            <FiltersModal
                open={isFiltersModalOpen}
                onClose={() => setFiltersModalOpen(false)}
                setVersion={handleVersionChange}
                onSearchChange={handleSearchChange}
                setTimezone={handleStatusTimezone}
                searchValue={searchValue}
                setStatus={handleStatusChange}
                status={status}
                timezone={zone}
                version={version}
            />
            <Button variant="outlined" onClick={() => setFiltersModalOpen(true)}>Фильтра</Button>
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
