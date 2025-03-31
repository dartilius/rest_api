'use client';
import './customPagination.scss';
import { ChangeEvent } from 'react';
import { usePathname, useSearchParams, useRouter } from 'next/navigation';

const CustomPagination = ({ totalItems }: { totalItems: number }) => {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const router = useRouter();

    const currentPage = Number(searchParams.get('page')) || 1;
    const itemsPerPage = Number(searchParams.get('limit')) || 10;

    const createPageURL = (pageNumber: number, limit: number = itemsPerPage) => {
        const params = new URLSearchParams(searchParams);
        params.set('page', pageNumber.toString());
        params.set('limit', limit.toString());
        return `${pathname}?${params.toString()}`;
    };

    const totalPages = Math.ceil(totalItems / itemsPerPage);

    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);

    const handlePageChange = (pageNumber: number, limit?: number) => {
        router.push(createPageURL(pageNumber, limit), { scroll: false });
    };

    return (
        <div className="pagination-container">
            <div className="pagination-info">
                <span>
                    Показано {startItem}-{endItem} из {totalItems}
                </span>
                <select
                    className="items-per-page-select"
                    value={itemsPerPage}
                    onChange={(event: ChangeEvent<HTMLSelectElement>) => {
                        handlePageChange(1, Number(event.target.value));
                    }}
                >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                </select>
            </div>
            <div className="pagination-controls">
                <button
                    className="pagination-button"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                >
                    &#8592;
                </button>
                <button
                    className="pagination-button"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                >
                    &#8594;
                </button>
            </div>
        </div>
    );
};

export default CustomPagination;
