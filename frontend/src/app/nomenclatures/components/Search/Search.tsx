import { InputLabel, OutlinedInput, TextField } from '@mui/material';

type SearchProps = {
    searchValue: string;
    onSearchChange: any;
    placeholder: string;
};


export const Search = (props: SearchProps) => {
    const { searchValue, onSearchChange, placeholder } =
        props;

    return (
        <TextField
            id="search-outlined"
            label={placeholder}
            variant="outlined"
            type='text'
            value={searchValue}
            onChange={onSearchChange}
            fullWidth
        />

    )
}