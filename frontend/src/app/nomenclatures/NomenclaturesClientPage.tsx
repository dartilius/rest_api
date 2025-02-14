'use client'

import {ChangeEvent, useEffect, useState} from "react";
import { Box, Button, Paper } from "@mui/material";
import './nomenclatures.scss'
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";
import TableComponent from "@/components/Ui/Table/Table";
import { useFetchNomenclatures } from "@/hooks/useFetchNomenclatures";
import { useDebounce } from "@/hooks/useDebounce";
import FiltersModal from "./components/FiltersModal";
import {INomenclatureResults} from "@/interfaces/Nomenclatures.interface";
import {useRouter, useSearchParams} from "next/navigation";
import {getNomenclatures} from "@/app/nomenclatures/page";
import {API_URL} from "@/config/api.config";
import {getClientAccessToken} from "@/utils";
import {useQuery} from "@tanstack/react-query";

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

export default function NomenclaturesPage({initialData}: {initialData: INomenclatureResults[]}) {
    const [page, setPage] = useState(1);
    const [limit, setLimit] = useState(10);
    const [searchValue, setSearchValue] = useState<string>("");
    const [status, setStatus] = useState<string>("");
    const [zone, setZone] = useState<string>("");
    const [version, setVersion] = useState<string>("");
    const [nomenclatures, setNomenclatures] = useState(initialData);
    const [loading, setLoading] = useState(false);
    const debouncedSearchValue = useDebounce(searchValue, 500);

    const router = useRouter();
    const searchParams = useSearchParams();

    // Обновление URL с фильтрами
    const updateUrlWithFilters = () => {
        const newParams = new URLSearchParams();

        if (searchValue) newParams.set("name", searchValue);
        if (status) newParams.set("status", status);
        if (zone) newParams.set("timezone", zone);
        if (version) newParams.set("version", version);

        router.push(`/?${newParams.toString()}`);
    };

    const {data, isLoading, refetch} = useQuery({
        queryFn: () => getNomenclatures({page, limit, name: searchValue, status, timezone: zone, version}),
        queryKey: ["nomenclatures", page, limit, searchValue, status, zone, version],
        enabled: false,
    })


    // const { nomenclatures, isError, isLoading, error, totalItems } = useFetchNomenclatures({
    //     page,
    //     limit,
    //     search: debouncedSearchValue,
    //     status: status,
    //     timezone: zone,
    //     version: version,
    // });

    // if (isError) console.error(error);

    const [isFiltersModalOpen, setFiltersModalOpen] = useState(false);

    const handleSearchChange = (searchValue: string) => {
        setSearchValue(searchValue);
        updateUrlWithFilters();
    };

    const handleStatusChange = (status: string) => {
        setStatus(status);
        updateUrlWithFilters();
    };

    const handleStatusTimezone = (zone: string) => {
        setZone(zone);
        updateUrlWithFilters();
    };

    const handleVersionChange = (version: string) => {
        setVersion(version);
        updateUrlWithFilters();
    };

    useEffect(() => {
        refetch().catch((data) => setNomenclatures(data.results));
        // setNomenclatures(data)
    }, [page, limit, status, version, searchValue, zone])

    // useEffect(() => {
    //     const params = new URLSearchParams(searchParams.toString());
    //     const page = params.get("page") ?? "1";
    //     const limit = params.get("limit") ?? "10";
    //     const name = params.get("name") ?? "";
    //     const status = params.get("status") ?? "";
    //     const timezone = params.get("timezone") ?? "";
    //     const version = params.get("version") ?? "";
    //
    //     setSearchValue(name);
    //     setStatus(status);
    //     setZone(timezone);
    //     setVersion(version);
    //
    //     // Выполняем запрос для обновления данных с новыми параметрами
    //     // getNomenclatures({ page, limit, name, status, timezone, version })
    //     //     .then(data => setNomenclatures(data.results))
    //     //     .catch(err => console.error(err));
    // }, [searchParams]);

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
                loading={loading}
            />
            <CustomPagination
                totalItems={nomenclatures.length}
                itemsPerPage={limit}
                setItemsPerPage={setLimit}
                currentPage={page}
                setCurrentPage={setPage}
            />
        </Paper>
    );
}
