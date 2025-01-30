import { timezonesArray } from "@/types/timeZone";
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";

interface TimezoneSelectProps {
    timezone: string;
    setTimezone: (status: string) => void;
}

const TimezoneSelect = ({ timezone, setTimezone }: TimezoneSelectProps) => {

    return (
        <FormControl fullWidth>
            <InputLabel id="timezone-label">Часовой пояс</InputLabel>
            <Select
                labelId="timezone-label"
                id="select-timezone"
                value={timezone}
                defaultValue={timezone}
                onChange={(event) => setTimezone(event.target.value as string)}
                label="Часовой пояс"

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

export default TimezoneSelect;
