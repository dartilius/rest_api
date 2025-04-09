"use client";

import { useRouter, useSearchParams } from 'next/navigation';
import { useMemo } from 'react';

type PaginationProps = {
    currentPage: number; // можно будет удалить, если будем использовать только из URL
    totalPages: number;
}

export function Pagination({ currentPage, totalPages }: PaginationProps) {
    const router = useRouter();
    const searchParams = useSearchParams();

    const pageFromUrl = useMemo(() => {
        const page = searchParams.get('page');
        return page ? parseInt(page, 10) : 1;
    }, [searchParams]);

    const handlePageChange = (page: number) => {
        const params = new URLSearchParams(searchParams.toString());
        params.set('page', page.toString());
        router.push(`?${params.toString()}`);
    };

    return (
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', gap: '10px' }}>
            {Array.from({ length: totalPages || 1 }, (_, index) => {
                const pageNumber = index + 1;
                const isActive = pageFromUrl === pageNumber;

                return (
                    <button
                        key={index}
                        onClick={() => handlePageChange(pageNumber)}
                        style={{
                            padding: '8px 12px',
                            border: '1px solid #ccc',
                            background: isActive ? '#007bff' : '#fff',
                            color: isActive ? '#fff' : '#000',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        {pageNumber}
                    </button>
                );
            })}
        </div>
    );
}
