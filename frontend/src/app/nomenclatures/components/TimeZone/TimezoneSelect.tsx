import { timezonesArray } from "@/types/timeZone";
import { FormControl, MenuItem, Select } from "@mui/material";
import {usePathname, useRouter, useSearchParams} from "next/navigation";
import {useEffect, useState} from "react";
import {handleQueryParamChange} from "@/utils";

export const TimezoneSelect = () => {

    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const currentTimezone = searchParams.get("timezone") || '';
    const [timezone, setTimezone] = useState<string>(currentTimezone);

    useEffect(() => {
        setTimezone(currentTimezone);
    }, [currentTimezone]);

    const handleTimezoneChange = (value: string) => {
        handleQueryParamChange(router, pathname, searchParams, 'timezone', value);
    };

    return (
        <FormControl fullWidth>
            <Select
                value={timezone}
                defaultValue={timezone}
                onChange={(event) => handleTimezoneChange(event.target.value as string)}
                style={{ color: 'black' }}
            >
                {timezonesArray.map((item, key) => (
                    <MenuItem key={key} value={item.value}>
                        {item.label}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>

    );
};