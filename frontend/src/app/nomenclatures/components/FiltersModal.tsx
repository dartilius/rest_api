import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, Typography } from "@mui/material";
import { useState, useEffect, ChangeEvent } from "react";
import { Search, StatusSelect, TimezoneSelect, VersionSelect } from './index'

interface FiltersModalProps {
  open: boolean;
  onClose: () => void;
  setVersion: (version: string) => void;
  setStatus: (status: string) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  setTimezone: (timezone: string) => void;
  timezone: string;
  version: string;
  status: string;
}

const FiltersModal = ({
  onClose,
  onSearchChange,
  open,
  searchValue,
  setStatus,
  setTimezone,
  setVersion,
  status,
  timezone,
  version,
}: FiltersModalProps) => {

  // Локальные состояния для фильтров
  const [localSearchValue, setLocalSearchValue] = useState(searchValue);
  const [localStatus, setLocalStatus] = useState(status);
  const [localTimezone, setLocalTimezone] = useState(timezone);
  const [localVersion, setLocalVersion] = useState(version);

  // Синхронизация начальных значений с props
  useEffect(() => {
    setLocalSearchValue(searchValue);
    setLocalStatus(status);
    setLocalTimezone(timezone);
    setLocalVersion(version);
  }, [searchValue, status, timezone, version]);

  const handleApplyFilters = () => {
    // Обновление значений в родительском компоненте
    onSearchChange(localSearchValue);
    setStatus(localStatus);
    setTimezone(localTimezone);
    setVersion(localVersion);

    // Закрытие модального окна
    onClose();
  };

  const clearFilter = () => {
    setLocalSearchValue('')
    setLocalStatus('')
    setLocalTimezone('')
    setLocalVersion('')
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Фильтры</DialogTitle>
      <DialogContent>
        <Box display="flex" flexDirection="column" gap={2}>
          <Typography variant="subtitle1">Поиск</Typography>
          <Search
            searchValue={localSearchValue}
            onSearchChange={(event: ChangeEvent<HTMLInputElement>) => setLocalSearchValue(event.target.value)}
            placeholder="Введите значение для поиска"
          />

          <Typography variant="subtitle1">Версия</Typography>
          <VersionSelect version={localVersion} setVersion={setLocalVersion} />

          <Typography variant="subtitle1">Статус</Typography>
          <StatusSelect status={localStatus} setStatus={setLocalStatus} />

          <Typography variant="subtitle1">Часовой пояс</Typography>
          <TimezoneSelect timezone={localTimezone} setTimezone={setLocalTimezone} />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={clearFilter} color='warning'>Сбросить</Button>
        <Button onClick={onClose} color="secondary">Отмена</Button>
        <Button onClick={handleApplyFilters} variant="contained" color="primary">
          Применить фильтры
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FiltersModal;
