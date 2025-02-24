'use client';

import { useEffect, useState } from 'react';
import {useRouter, useSearchParams} from "next/navigation";
import { Button } from "@mui/material";
import FiltersModal from './FiltersModal';

export const FiltersModalWrapper = ({ openModalFilters }: { openModalFilters: boolean }) => {
    const router = useRouter();
    const searchParams = useSearchParams()
    const [open, setOpen] = useState(openModalFilters);

    const toggleModal = (isOpen: boolean) => {
        const params = new URLSearchParams(searchParams);
        if (isOpen) {
            params.set('openModalFilters', 'true');
        } else {
            params.delete('openModalFilters');
        }
        router.push(`?${params.toString()}`);
        setOpen(isOpen);
    };

    useEffect(() => {
        setOpen(openModalFilters);
    }, [openModalFilters]);

    return (
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <Button onClick={() => toggleModal(true)} variant='contained' color='secondary' style={{maxWidth: '120px'}}>Фильтры</Button>
            <FiltersModal open={open} onClose={() => toggleModal(false)} />
        </div>
    );
};
