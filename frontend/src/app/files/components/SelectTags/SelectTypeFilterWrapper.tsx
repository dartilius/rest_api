'use client'

import { useState } from 'react'
import SelectTags from '@/app/files/components/SelectTags/SelectTags'
import { usePathname, useRouter, useSearchParams } from "next/navigation";

function SelectTagsFilterWrapper() {
    const searchParams = useSearchParams();
    const pathname = usePathname();
    const router = useRouter();

    const handleSelectTagsFile = (selectedTags: string[]) => {
        const params = new URLSearchParams(searchParams);

        // Удаляем все текущие теги
        params.delete('tags');

        // Добавляем новые теги
        selectedTags.forEach(tag => {
            params.append('tags', tag);
        });

        // Сброс страницы при фильтрации
        params.set('page', '1');

        router.push(`${pathname}?${params.toString()}`);
    };

    return (
        <SelectTags
            label="Выбрать"
            onChange={(tags) => handleSelectTagsFile(tags.map((tag) => tag.name))}
        />
    )
}

export default SelectTagsFilterWrapper;
