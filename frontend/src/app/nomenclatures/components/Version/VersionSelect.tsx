'use client'

import { useGetVersions } from "@/hooks/useFetchNomenclatures";
import { FormControl, MenuItem, Select, Alert } from "@mui/material";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import {handleQueryParamChange} from "@/utils";

export const VersionSelect = () => {
    const { versionsList, error, isError } = useGetVersions();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();

    const currentVersion = searchParams.get('version')?.toString() || '';
    const [version, setVersion] = useState<string>(currentVersion);

    useEffect(() => {
        setVersion(currentVersion);
    }, [currentVersion]);

    const handleVersionChange = (value: string) => {
        handleQueryParamChange(router, pathname, searchParams, 'version', value);
    };

    if (isError) {
        return (
            <Alert severity="error">
                Ошибка загрузки версий: {error?.message || 'Неизвестная ошибка'}
            </Alert>
        );
    }

    const uniqueVersions = Array.from(new Set(versionsList?.versions || []));

    return (
        <FormControl fullWidth>
            <Select
                value={version}
                onChange={(e) => handleVersionChange(e.target.value)}
                displayEmpty
                style={{backgroundColor: 'white', borderRadius: '4px'}}
            >
                <MenuItem value="">
                    <em>Все версии</em>
                </MenuItem>
                {uniqueVersions.map((item) => (
                    <MenuItem key={item || 'no-version'} value={item}>
                        {item || 'Без версии'}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
};