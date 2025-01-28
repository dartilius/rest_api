'use client'

import { useEffect, useState } from "react";
import { Paper, Button } from "@mui/material";
import './nomenclatures.scss'
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";
import TableComponent from "@/components/Ui/Table/Table";
import { useFetchNomenclatures } from "@/hooks/useFetchNomenclatures";

const columns = [
    { id: "id", label: "ID", minWidth: 100 },
    { id: "name", label: "Название", minWidth: 170 },
    { id: "timezone", label: "Часовой пояс", minWidth: 170 },
    { id: "version", label: "Версия", minWidth: 170 },
    { id: "last_answer", label: "Последний ответ", minWidth: 120 },
    { id: "status", label: "Статус", minWidth: 120 },
];

export default function NomenclaturesPage() {
    const [page, setPage] = useState(1); // Начинаем с первой страницы
    const [limit, setLimit] = useState(10);
    const [zone, setZone] = useState<string>("");
    const [status, setStatus] = useState<string>("");
    const [token, setToken] = useState<string | null>(null); // Token state
    const statusTypes = [0, 1, 2, 3];

    // Check if localStorage is available on the client-side
    useEffect(() => {
        if (typeof window !== "undefined") {
            const storedToken = localStorage.getItem("accessToken");
            setToken(storedToken);
        }
    }, []); // Runs once after component mounts

    console.log(token);


    const { fetchData, nomenclatures, totalItems, loading } = useFetchNomenclatures(
        {
            token,
            page,
            limit,
            timezone: zone,
            status
        }
    );

    useEffect(() => {
        if (token) {
            fetchData(); // Only fetch data if the token is available
        }
    }, [page, limit, token]); // Triggered when page, limit, or token changes

    return (
        <Paper sx={{ width: "100%", overflow: "hidden" }}>
            <Button onClick={fetchData}>Обновить данные</Button>
            <TableComponent
                data={nomenclatures}
                columns={columns}
                link="nomenclatures"
                limit={limit}
                loading={loading}
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
