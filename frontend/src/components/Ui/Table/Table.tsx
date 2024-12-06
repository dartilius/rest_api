/* eslint-disable @typescript-eslint/no-explicit-any */
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import TableRowsLoader from "./TableLoader";
import Link from "next/link";

interface Props {
    data: any;
    columns: any;
    link: string;
    limit: number;
}

const TableComponent = ({ data, columns, link, limit }: Props) => {
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
                    {(!data || data.length === 0) ? (
                        <TableRowsLoader rowsNum={limit} columnsNum={columns.length} />
                    ) : (
                        data.map((row: any) => (
                            <TableRow hover role="checkbox" tabIndex={-1} key={row.id}>
                                {columns.map((column: any) => {
                                    const value = row[column.id];
                                    return (
                                        <TableCell key={column.id} className="font-subtitle">
                                            <Link href={`/${link}/${row.id}`}>{value}</Link>
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
}

export default TableComponent;