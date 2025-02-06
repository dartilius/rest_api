import { useGetVersions } from "@/hooks/useFetchNomenclatures";
import { FormControl, InputLabel, MenuItem, Select, Skeleton } from "@mui/material";

interface TimezoneSelectProps {
    version: string;
    setVersion: (status: string) => void;
}

export const VersionSelect = ({ setVersion, version }: TimezoneSelectProps) => {
    const { versionsList, error, isError, isLoading } = useGetVersions()

    if (isError) console.error(error)

    console.log(versionsList);

    return (

        <FormControl fullWidth>
            <InputLabel id="timezone-label">Версия</InputLabel>
            <Select
                labelId="timezone-label"
                id="select-timezone"
                value={version}
                defaultValue={version}
                onChange={(event) => setVersion(event.target.value as string)}
                label="Версия"

                style={{ color: 'black' }}
            >
                {isLoading ? (
                    <Skeleton animation="wave" variant="text" />
                ) : (
                    versionsList.versions.map((item, key) => (
                        <MenuItem key={key} value={item}>
                            {item === '' ? 'Без версии' : item}
                        </MenuItem>
                    )))}

            </Select>
        </FormControl >


    );
};
