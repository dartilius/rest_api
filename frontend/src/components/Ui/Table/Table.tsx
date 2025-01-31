import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import TableRowsLoader from "./TableLoader";
import Link from "next/link";
import { Box } from "@mui/material";
import { convertStatus } from "@/types/checkStatus";

interface Props {
    data: any;
    columns: any;
    link: string;
    limit: number;
    loading?: boolean;
}

const statusColors: Record<any, string> = {
    0: "#4caf50", // Зеленый для онлайн
    1: "#ff9800", // Оранжевый для оффлайн 5 минут
    2: "#f44336", // Красный для оффлайн час
    null: "#9e9e9e", // Серый для "Не выходила в сеть"
};

const TableComponent = ({ data, columns, link, limit, loading }: Props) => {

    if (!data) return <>WTF</>

    return (
        <TableContainer>
            <Table stickyHeader aria-label="sticky table" className="rounded">
                <TableHead>
                    <TableRow>
                        {columns.map((column: any) => (
                            <TableCell key={column.id} style={{ minWidth: column.minWidth }} className="font-title">
                                {column.label}
                            </TableCell>
                        ))}
                    </TableRow>
                </TableHead>
                <TableBody>
                    {loading ? (
                        <TableRowsLoader rowsNum={limit} columnsNum={columns.length} />
                    ) : (
                        data.map((row: any) => (
                            <TableRow hover role="checkbox" tabIndex={-1} key={row.id}>
                                {columns.map((column: any) => {
                                    const value = row[column.id];
                                    return (
                                        <TableCell key={column.id} className="font-subtitle">
                                            {column.id === "status" ? (
                                                <Box
                                                    sx={{
                                                        display: "inline-block",
                                                        padding: "4px 8px",
                                                        borderRadius: "8px",
                                                        backgroundColor: statusColors[value],
                                                        color: "white",
                                                    }}
                                                >
                                                    {convertStatus(value)}
                                                </Box>
                                            ) : (
                                                <Link href={`/${link}/${row.id}`}>{value}</Link>
                                            )}
                                        </TableCell>
                                    );
                                })}
                            </TableRow>
                        ))
                    )}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

export default TableComponent;
