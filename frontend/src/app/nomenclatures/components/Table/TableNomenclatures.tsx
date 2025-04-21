import {Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@mui/material";
import Link from "next/link";
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";
import {getStatusColor} from "@/utils";
import {convertStatus} from "@/types/checkStatus";
import {NomenclatureActions} from "@/app/nomenclatures/components";
import styles from '@/app/nomenclatures/Nomenclatures.module.scss'

const columns = [
    {id: "name", label: "Название", minWidth: 170, maxWidth: 170},
    {id: "timezone", label: "Часовой пояс", maxWidth: 120, minWidth: 120},
    {id: "version", label: "Версия", maxWidth: 120, minWidth: 120},
    {id: "last_answer", label: "Последний ответ", minWidth: 120, maxWidth: 120},
    {id: "status", label: "Статус", minWidth: 120, maxWidth: 120},
    {id: "actions", label: "Действия", minWidth: 120, maxWidth: 120},
];

type Props = {
    data: any
    count: any
}

export function TableNomenclatures(props: Props) {
    const { data, count } = props

    return (
        <TableContainer
            component={Box}
            className={styles.custom_scroll}
            sx={{
                maxWidth: '100%',
                maxHeight: '760px',
                height: '100%',
                overflow: 'hidden',
                overflowY: 'auto',
                overflowX: 'auto',
                borderRadius: '8px',
                backgroundColor: 'white',
            }}
        >
            <Table stickyHeader aria-label="sticky table" className="rounded">
                <TableHead>
                    <TableRow>
                        {columns.map((column: any) => (
                            <TableCell
                                key={column.id}
                                sx={{
                                    minWidth: column.minWidth,
                                    maxWidth: column.maxWidth,
                                    whiteSpace: "nowrap",
                                }}
                                className="font-title"
                            >
                                {column.label}
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody style={{backgroundColor: "white"}}>
                    {data?.map((row: any) => (
                        <TableRow hover role="checkbox" tabIndex={-1} key={row?.id}>
                            {columns?.map((column: any) => {
                                const value = row[column?.id];
                                return (
                                    <TableCell
                                        key={column.id}
                                        sx={{
                                            minWidth: column.minWidth,
                                            maxWidth: column.maxWidth,
                                            whiteSpace: "nowrap",
                                            overflow: "hidden",
                                            textOverflow: "ellipsis",
                                        }}
                                        className="font-subtitle"
                                    >
                                        {column.id === "status" ? (
                                            <Box
                                                sx={{
                                                    display: "inline-block",
                                                    padding: "4px 8px",
                                                    borderRadius: "8px",
                                                    backgroundColor: getStatusColor(value),
                                                    color: "white",
                                                }}
                                            >
                                                {convertStatus(value)}
                                            </Box>
                                        ) : column.id === "actions" ? (
                                            <NomenclatureActions id={row.id} />
                                        ) : (
                                            <Link href={`/nomenclatures/${row.id}`}>{value}</Link>
                                        )}
                                    </TableCell>
                                );
                            })}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
            <CustomPagination totalItems={count} />
        </TableContainer>
    );
}