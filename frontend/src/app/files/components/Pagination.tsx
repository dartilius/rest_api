"use client";

import { useRouter, useSearchParams } from 'next/navigation';

type PaginationProps = {
    currentPage: number;
    totalPages: number;
}

export function Pagination({ currentPage, totalPages }: PaginationProps) {
    const router = useRouter();
    const searchParams = useSearchParams();

    const handlePageChange = (page: number) => {
        const params = new URLSearchParams(searchParams.toString());
        params.set('page', page.toString());
        router.push(`?${params.toString()}`);
    };

    return (
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', gap: '10px' }}>
            {Array.from({ length: totalPages || 1 }, (_, index) => (
                <button
                    key={index}
                    onClick={() => handlePageChange(index + 1)}
                    style={{
                        padding: '8px 12px',
                        border: '1px solid #ccc',
                        background: currentPage === index + 1 ? '#007bff' : '#fff',
                        color: currentPage === index + 1 ? '#fff' : '#000',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    {index + 1}
                </button>
            ))}
        </div>
    );
}
