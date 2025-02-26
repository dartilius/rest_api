'use client';
import { ChangeEvent, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useDebouncedCallback } from "use-debounce";
import { TextField } from "@mui/material";
import {handleQueryParamChange} from "@/utils";

export function Search() {
    const searchParams = useSearchParams();
    const pathname = usePathname();
    const router = useRouter();
    const currentSearchValue = searchParams?.get('name') || '';
    const [searchValue, setSearchValue] = useState<string>(currentSearchValue);

    const handleSearch = useDebouncedCallback((value: string) => {
        handleQueryParamChange(router, pathname, searchParams, 'name', value);
    }, 500);

    useEffect(() => {
        setSearchValue(currentSearchValue);
    }, [currentSearchValue]);

    return (
            <TextField
                variant="outlined"
                fullWidth
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                    setSearchValue(e.target.value);
                    handleSearch(e.target.value);
                }}
                value={searchValue}
                style={{backgroundColor: 'white', borderRadius: '4px'}}
            />
    );
}
