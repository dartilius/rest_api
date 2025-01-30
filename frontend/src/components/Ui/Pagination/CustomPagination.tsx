import React from "react";
import './customPagination.scss';

interface CustomPaginationProps {
    totalItems: number;
    itemsPerPage: number;
    setItemsPerPage: (count: number) => void;
    currentPage: number;
    setCurrentPage: (page: number) => void;
}

const CustomPagination: React.FC<CustomPaginationProps> = ({
    totalItems,
    itemsPerPage,
    setItemsPerPage,
    currentPage,
    setCurrentPage,
}) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    const handlePreviousPage = () => {
        if (currentPage > 1) {
            setCurrentPage(currentPage - 1);
        }
    };

    const handleNextPage = () => {
        if (currentPage < totalPages) {
            setCurrentPage(currentPage + 1);
        }
    };

    const handleItemsPerPageChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setItemsPerPage(Number(event.target.value));
        setCurrentPage(1); // Сброс на первую страницу
    };

    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);

    return (
        <div className="pagination-container">
            <div className="pagination-info">
                <span>
                    Показано {startItem}-{endItem} из {totalItems}
                </span>
                <select
                    className="items-per-page-select"
                    value={itemsPerPage}
                    onChange={handleItemsPerPageChange}
                >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                </select>
            </div>
            <div className="pagination-controls">
                <button
                    className="pagination-button"
                    onClick={handlePreviousPage}
                    disabled={currentPage === 1}
                >
                    &#8592; {/* Стрелка влево */}
                </button>
                <button
                    className="pagination-button"
                    onClick={handleNextPage}
                    disabled={currentPage === totalPages}
                >
                    &#8594; {/* Стрелка вправо */}
                </button>
            </div>
        </div>
    );
};

export default CustomPagination;
