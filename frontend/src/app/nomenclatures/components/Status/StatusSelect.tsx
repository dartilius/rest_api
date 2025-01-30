import { convertStatus } from "@/types/checkStatus";
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";

interface StatusSelectProps {
  status: string;
  setStatus: (status: string) => void;
}

const StatusSelect = ({ status, setStatus }: StatusSelectProps) => {
  const statusTypes = [0, 1, 2, 3];

  return (
    <FormControl fullWidth>
      <InputLabel id="status-label">Статус</InputLabel>
      <Select
        labelId="status-label"
        id="select-status"
        value={status}
        onChange={(event) => setStatus(event.target.value as string)}
        label="Статус"

        style={{ color: 'black' }}
      >
        {statusTypes.map((item) => (
          <MenuItem key={item} value={item}>
            {convertStatus(item)}
          </MenuItem>
        ))}
      </Select>
    </FormControl>

  );
};

export default StatusSelect;
