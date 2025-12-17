import { Skeleton, TableCell, TableRow } from "@mui/material";

interface TableRowsLoaderProps {
    rowsNum: number; // Количество строк
    columnsNum: number; // Количество ячеек (TableCell) в каждой строке
}

const TableRowsLoader = ({ rowsNum, columnsNum }: TableRowsLoaderProps) => {
    return [...Array(rowsNum)].map((_, rowIndex) => (
        <TableRow key={rowIndex}>
            {[...Array(columnsNum)].map((_, cellIndex) => (
                <TableCell key={cellIndex}>
                    <Skeleton animation="wave" variant="text" />
                </TableCell>
            ))}
        </TableRow>
    ));
};

export default TableRowsLoader;