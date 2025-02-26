import fetchNomenclatures from "@/services/NomenclaturesService";
import {Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow} from "@mui/material";
import Link from "next/link";
import CustomPagination from "@/components/Ui/Pagination/CustomPagination";
import {getStatusColor} from "@/utils";
import {convertStatus} from "@/types/checkStatus";

const columns = [
    {id: "name", label: "Название", minWidth: 170},
    {id: "timezone", label: "Часовой пояс", maxWidth: 170},
    {id: "version", label: "Версия", maxWidth: 170},
    {id: "last_answer", label: "Последний ответ", minWidth: 120},
    {id: "status", label: "Статус", minWidth: 120},

];

type Props = {
    name: string;
    currentPage: number
    limit: number
    version: string;
    status: string;
    timezone: string;
}

export async function TableNomenclatures(props: Props) {
    const { name, currentPage, limit, version, status, timezone } = props

    const listNomenclatures = await fetchNomenclatures({page: currentPage, limit, name, version, status, timezone})
    return (
        <TableContainer style={{borderRadius: '8px'}}>

            <Table stickyHeader aria-label="sticky table" className="rounded">
                <TableHead>
                    <TableRow>
                        {columns.map((column: any) => (
                            <TableCell key={column.id} style={{minWidth: column.minWidth}} className="font-title">
                                {column.label}
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody style={{backgroundColor: "white"}}>
                    {listNomenclatures.results.map((row: any) => (
                        <TableRow hover role="checkbox" tabIndex={-1} key={row?.id}>
                            {columns?.map((column: any) => {
                                const value = row[column?.id];
                                return (
                                    <TableCell key={column.id} className="font-subtitle">
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
            <CustomPagination totalItems={listNomenclatures.count} />
        </TableContainer>
    );
}