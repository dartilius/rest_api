'use client'
import {FormControl, MenuItem, Select} from "@mui/material";
import {usePathname, useRouter, useSearchParams} from "next/navigation";
import {useDebouncedCallback} from "use-debounce";
import {handleQueryParamChange} from "@/utils";

const arrayOfTypesFile = [
    {id: '', label: 'Весь список'},
    { id: '0', label: 'Музыка' },
    { id: '1', label: 'Видео' },
    { id: '2', label: 'Изображение' },
    { id: '3', label: 'Бегущая строка' },
    { id: '4', label: 'Реклама' }
];

function SelectType() {

    const searchParams = useSearchParams();
    const pathname = usePathname();
    const router = useRouter();
    const selectedType = searchParams.get('file_type') || '';

    const handleSelectTypeFile = useDebouncedCallback((value: string) => {
        handleQueryParamChange(router, pathname, searchParams, 'file_type', value);
    }, 1000);

    return (
        <FormControl sx={{width: '35%'}}>
            <Select
                value={selectedType}
                onChange={(event) => {
                    const selectedType = event.target.value as string;
                    handleSelectTypeFile(selectedType);
                }}
                style={{ color: 'black', backgroundColor: 'white', borderRadius: '4px',  maxHeight: '52px' }}
                displayEmpty
            >
                {arrayOfTypesFile.map((item) => (
                    <MenuItem key={item.id} value={item.id}>
                        {item.label}
                    </MenuItem>
                ))}
            </Select>
        </FormControl>
    );
}

export default SelectType;