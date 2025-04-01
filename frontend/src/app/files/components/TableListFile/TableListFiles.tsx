'use client'

import React, { useState } from "react";
import {deleteFile, fetchFilesById} from "@/services/FilesService";
import {
    Box,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Collapse,
    IconButton
} from "@mui/material";
import { convertSizeFile } from "@/utils";
import {guessType} from "@/utils/convertTypeFile";
import Image from "next/image";
import {useNotification} from "@/hooks/useNotification";
import styles from './TableListFile.module.scss'
import {gifDelete, gifEdit, gifView, staticDelete, staticEdit, staticView} from "@/styles";
import {useRouter} from "next/navigation";

type Props = {
    data: any;
};

type FetchFileResponse = {
    id: string;
    length: string;
    size: number;
    name: string;
    type: string;
    source: string;
    tags: { id: string; name: string }[];
    url: string;
    hash: string;
    created: string;
};

const columns = [
    { id: "name", label: "Название", minWidth: 170, maxWidth: 170 },
    { id: "size", label: "Размер", maxWidth: 120, minWidth: 120 },
    { id: "type", label: "Тип", maxWidth: 120, minWidth: 120 },
    { id: "action", label: "Действие", maxWidth: 120, minWidth: 120 }
];

const TableListFiles = (props: Props) => {

    const {data} = props

    const [fileData, setFileData] = useState<Record<string, FetchFileResponse>>({});
    const [hoveredImages, setHoveredImages] = useState<Record<string, { edit: string; delete: string; view: string }>>({});

    const { showNotification } = useNotification()
    const router = useRouter();

    const handleMoreDetails = async (id: string) => {
        if (fileData[id]) {
            setFileData(prev => {
                const newData = { ...prev };
                delete newData[id];
                return newData;
            });
        } else {
            const res = await fetchFilesById({ id });
            if (res && typeof res !== "string") {
                setFileData(prev => ({ ...prev, [id]: res }));
            }
        }
    };

    const handleMouseEnter = (id: string, type: "edit" | "delete" | "view") => {
        setHoveredImages(prev => ({
            ...prev,
            [id]: {
                ...prev[id],
                [type]: type === "edit" ? gifEdit : type === "delete" ? gifDelete : gifView
            }
        }));
    };

    const handleMouseLeave = (id: string, type: "edit" | "delete" | "view") => {
        setHoveredImages(prev => ({
            ...prev,
            [id]: {
                ...prev[id],
                [type]: type === "edit" ? staticEdit : type === "delete" ? staticDelete : staticView
            }
        }));
    };

    const previewFile = (file: FetchFileResponse, fileType: string) => {
        if (!file || !fileType) return null;

        const type = guessType(fileType)

        switch (type) {
            case "image":
                return <Image src={file.url} alt={file.name} width={200} height={200} style={{ borderRadius: "8px", objectFit: "cover" }} />;
            case "video":
                return <video controls width="300"><source src={file.url} type="video/mp4" />Ваш браузер не поддерживает видео.</video>;
            case "audio":
                return <audio controls><source src={file.url} type="audio/mpeg" />Ваш браузер не поддерживает аудио.</audio>;
            default:
                return <strong>Предпросмотр недоступен</strong>;
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text)
            .then(() => showNotification('Hash скопирован!', 'success'))
            .catch(err =>  showNotification('Не удалось скопировать Hash!', 'error'));
    };

    const handleDelete = async (id: string) => {
        try {
            await deleteFile(id)
            showNotification('Файл удален!', 'success')
            router.refresh()
        } catch (error) {
            console.log(error);
            showNotification('Не удалось удалить фалй', 'error')
        }
    }


    return (
        <TableContainer
            component={Box}
            sx={{ maxWidth: "100%", maxHeight: "1200px", overflow: "auto", borderRadius: "8px", backgroundColor: "white" }}
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
                        <React.Fragment key={row.id}>
                            <TableRow hover role="checkbox" tabIndex={-1}>
                                {columns.map(column => {
                                    let value = row[column.id];
                                    if (column.id === "size") value = convertSizeFile(row.size);

                                    return (
                                        <TableCell key={column.id}>
                                            {value}
                                            {column.id === "action" && (
                                                <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', maxHeight: '24px'}} key={row.id}>

                                                    <Image
                                                        src={hoveredImages[row.id]?.edit || staticEdit}
                                                        alt='edit'
                                                        width={24}
                                                        height={24}
                                                        onMouseEnter={() => handleMouseEnter(row.id, "edit")}
                                                        onMouseLeave={() => handleMouseLeave(row.id, "edit")}
                                                    />
                                                    <IconButton onClick={() => handleDelete(row.id)}>
                                                        <Image
                                                            src={hoveredImages[row.id]?.delete || staticDelete}
                                                            alt='delete'
                                                            width={24}
                                                            height={24}
                                                            onMouseEnter={() => handleMouseEnter(row.id, "delete")}
                                                            onMouseLeave={() => handleMouseLeave(row.id, "delete")}
                                                        />
                                                    </IconButton>
                                                    <IconButton onClick={() => handleMoreDetails(row.id)}>
                                                        <Image
                                                            src={hoveredImages[row.id]?.view || staticView}
                                                            alt='view'
                                                            width={24}
                                                            height={24}
                                                            onMouseEnter={() => handleMouseEnter(row.id, "view")}
                                                            onMouseLeave={() => handleMouseLeave(row.id, "view")}
                                                        />
                                                    </IconButton>
                                                </div>
                                            )}
                                        </TableCell>
                                    );
                                })}
                            </TableRow>
                            {fileData[row.id] && (
                                <TableRow>
                                    <TableCell colSpan={columns.length}>
                                        <Collapse in={!!fileData[row.id]} timeout="auto" unmountOnExit>
                                            <Box sx={{ padding: 2, backgroundColor: "#f9f9f9", borderRadius: "4px" }}>
                                                <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between'}}>
                                                    <div
                                                        onClick={() => copyToClipboard(fileData[row.id]?.hash)}
                                                        className={styles.copy}
                                                    >
                                                        Hash: <Button variant='contained' color='inherit'>{fileData[row.id]?.hash.slice(0, 25) + '...'}</Button>
                                                    </div>
                                                    <div>Дата создания: {fileData[row.id].created}</div>
                                                </div>
                                                {(fileData[row.id]?.tags?.length ?? 0) > 1 && (
                                                    <div>Теги: {fileData[row.id]?.tags.map(tag => tag.name).join(", ")}</div>
                                                )}

                                                <Box mt={2} display='flex' flexDirection='row' justifyContent='center'>
                                                    {fileData[row.id] && fileData[row.id]?.name
                                                        ? previewFile(fileData[row.id], fileData[row.id].name)
                                                        : "Предпросмотр недоступен"}
                                                </Box>

                                            </Box>
                                        </Collapse>
                                    </TableCell>
                                </TableRow>
                            )}
                        </React.Fragment>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

export default TableListFiles;
