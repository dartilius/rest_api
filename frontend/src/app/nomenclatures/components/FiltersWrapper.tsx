'use client';

import {Box, Typography} from "@mui/material";
import {Search} from "@/app/nomenclatures/components/Search/Search";
import {VersionSelect} from "@/app/nomenclatures/components/Version/VersionSelect";
import {StatusSelect} from "@/app/nomenclatures/components/Status/StatusSelect";
import {TimezoneSelect} from "@/app/nomenclatures/components/TimeZone/TimezoneSelect";
import CreateNomenclature from "@/app/nomenclatures/components/CreateNomenclature/CreateNomenclature";

export const FiltersWrapper = () => {

    return (
        <Box display="flex" flexDirection="row" gap={2} width='100%'>
            <div style={{ display: 'flex', flexDirection: 'column', width: '100%'}}>
                <Typography variant="subtitle1">Поиск</Typography>
                <Search  nameQueryParams="name" label='Название'/>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <Typography variant="subtitle1">Версия</Typography>
                <VersionSelect />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <Typography variant="subtitle1">Статус</Typography>
                <StatusSelect />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <Typography variant="subtitle1">Часовой пояс</Typography>
                <TimezoneSelect />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <CreateNomenclature />
            </div>
        </Box>
    );
};
