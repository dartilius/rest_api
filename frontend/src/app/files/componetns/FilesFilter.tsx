// app/files-filter.tsx
"use client";

import { useSearchParams, useRouter } from "next/navigation";
import {ChangeEvent} from "react";

export default function FilesFilter() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const currentQuery = searchParams.get("query") || "";

    const handleSearch = (event: ChangeEvent<HTMLInputElement>) => {
        const newQuery = event.target.value;
        const params = new URLSearchParams(searchParams);

        if (newQuery) {
            params.set("query", newQuery);
        } else {
            params.delete("query");
        }

        router.push(`/?${params.toString()}`);
    };

    return (
        <input
            type="text"
            placeholder="Поиск файлов..."
            value={currentQuery}
            onChange={handleSearch}
        />
    );
}
