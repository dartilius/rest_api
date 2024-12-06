'use client'

import React, { useState } from "react";
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
    const [rowsPerPage, setRowsPerPage] = useState(5);
    const [zone, setZone] = useState<string>("");
    const [status, setStatus] = useState<string>("");
    const token = localStorage.getItem("accessToken");
    const statusTypes = [0, 1, 2, 3];

    const { fetchData, nomenclatures, totalItems } = useFetchNomenclatures(
        {
            token,
            page,
            limit: rowsPerPage,
            timezone: zone,
            status
        }
    );

    return (
        <Paper sx={{ width: "100%", overflow: "hidden" }}>
            <Button onClick={fetchData}>Обновить данные</Button>
            <TableComponent
                data={nomenclatures.slice((page - 1) * rowsPerPage, page * rowsPerPage)}
                columns={columns}
                link="nomenclatures"
                limit={rowsPerPage}
            />
            <CustomPagination
                totalItems={totalItems}
                itemsPerPage={rowsPerPage}
                setItemsPerPage={setRowsPerPage}
                currentPage={page}
                setCurrentPage={setPage}
            />
        </Paper>
    );
};


//limit * (pageNumber - 1)