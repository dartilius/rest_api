'use client'

import { useGetVersions } from "@/hooks/useFetchNomenclatures";
import { FormControl, MenuItem, Select, Skeleton, Alert } from "@mui/material";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import {handleQueryParamChange} from "@/utils";

export const VersionSelect = () => {
    const { versionsList, error, isError, isLoading } = useGetVersions();
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

    if (isLoading) {
        return (
            <Skeleton
                variant="rectangular"
                width="100%"
                height={56}
                sx={{
                    borderRadius: '4px',
                    mt: 1
                }}
            />
        );
    }

    const uniqueVersions = Array.from(new Set(versionsList?.versions || []));

    return (
        <FormControl fullWidth>
            <Select
                value={version}
                onChange={(e) => handleVersionChange(e.target.value)}
                displayEmpty
                sx={{
                    color: 'black',
                    '.MuiSelect-select': {
                        py: 1.5
                    }
                }}
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