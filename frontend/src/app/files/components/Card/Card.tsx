'use client'

import React, {useEffect, useState}  from "react";
import {fetchFilesById} from "@/services/FilesService";
import styles from './Card.module.scss'
import Image from "next/image";
import {Box, Button, Collapse, Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@mui/material";
import {convertSizeFile, getStatusColor} from "@/utils";
import {convertStatus} from "@/types/checkStatus";
import {NomenclatureActions} from "@/app/nomenclatures/components";
import Link from "next/link";
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";

type Props = {
    // id: string;
    // key: number;
    data: any;
}

type fetchFileResponse = {
    id: string;
    length: string;
    size: number;
    name: string;
    type: string;
    source: string;
    tags: Array<{
        id: string;
        name: string;
    }>
    url: string;
}

const columns = [
    { id: "name", label: "Название", minWidth: 170, maxWidth: 170 },
    { id: "size", label: "Размер", maxWidth: 120, minWidth: 120 },
    { id: "type", label: "Тип", maxWidth: 120, minWidth: 120 },
    { id: "action", label: "Действие", maxWidth: 120, minWidth: 120 }
];

function Card({ data }: Props) {
    const [expandedRow, setExpandedRow] = useState(null);
    const [fileData, setFileData] = useState<Record<string, fetchFileResponse>>({});

    const handleMoreDetails = async (id: string) => {
        if (fileData[id]) {
            // Если данные уже загружены, удаляем их (сворачиваем строку)
            setFileData(prev => {
                const newData = { ...prev };
                delete newData[id];
                return newData;
            });
        } else {
            // Если данных нет, загружаем их и разворачиваем строку
            const res = await fetchFilesById({ id });
            if (res && typeof res !== "string") {
                setFileData(prev => ({ ...prev, [id]: res }));
            }
        }
    };


    return (
        <TableContainer
            style={{ borderRadius: '8px' }}
            component={Box}
            sx={{ maxWidth: "100%", maxHeight: "1200px", overflow: "auto", borderRadius: "8px",backgroundColor: "white" }}
        >
            <Table stickyHeader>
                <TableHead>
                    <TableRow>
                        {columns.map(column => (
                            <TableCell key={column.id} sx={{ minWidth: column.minWidth, maxWidth: column.maxWidth }}>
                                {column.label}
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody>
                    {data?.map((row: any) => (
                        <React.Fragment key={row?.id}>
                            <TableRow hover role="checkbox" tabIndex={-1}>
                                {columns?.map((column: any) => {
                                    const value = row[column?.id];
                                    return (
                                        <TableCell key={column.id}>
                                            {value}
                                            {column.id === 'action' && (
                                                <Button onClick={() => handleMoreDetails(row.id)}>
                                                    {fileData[row.id] ? "Less" : "More"}
                                                </Button>
                                            )}
                                        </TableCell>
                                    );
                                })}
                            </TableRow>
                            {fileData[row.id] && (
                                <TableRow>
                                    <TableCell colSpan={columns.length}>
                                        <div style={{ padding: "10px", background: "#f9f9f9" }}>
                                            <p><strong>Название:</strong> {fileData[row.id].name}</p>
                                            <p><strong>Размер:</strong> {convertSizeFile(fileData[row.id].size)}</p>
                                            <p><strong>Тип:</strong> {fileData[row.id].type}</p>
                                            <p><strong>URL:</strong> <a href={fileData[row.id].url} target="_blank">{fileData[row.id].url}</a></p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )}
                        </React.Fragment>
                    ))}

                </TableBody>
            </Table>
        </TableContainer>
    );
}

export default Card;
