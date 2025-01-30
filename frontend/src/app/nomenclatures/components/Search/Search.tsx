import { OutlinedInput } from '@mui/material';
import { useState } from 'react'

type SearchProps = {
    searchValue: string;
    onSearchChange: any;
    onSearchSubmit: any;
    label: string;
    placeholder: string;
};


const Search = (props: SearchProps) => {
    const { searchValue, onSearchChange, onSearchSubmit, label, placeholder } =
        props;
    const handleKeyDown = (event: { key: string }) => {
        if (event.key === "Enter") {
            onSearchSubmit();
        }
    };

    return (
        <div>
            <OutlinedInput
                type='text'
                placeholder={placeholder}
                value={searchValue}
                onChange={onSearchChange}
                onKeyDown={handleKeyDown}
            />
        </div>
    )
}

export default Search