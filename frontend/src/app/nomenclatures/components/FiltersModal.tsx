'use client';

import {Dialog, DialogTitle, DialogContent, DialogActions, Button, Box, Typography, Tooltip} from "@mui/material";
import {Search, StatusSelect, TimezoneSelect, VersionSelect} from './index';
import {useRouter, useSearchParams} from "next/navigation";

interface FiltersModalProps {
  open: boolean;
  onClose: () => void;
}

const FiltersModal = ({ open, onClose }: FiltersModalProps) => {
    const router = useRouter();
    const searchParams = useSearchParams()
    const clearModalFilters = () => {
        const params = new URLSearchParams(searchParams);
        params.delete('name');
        params.delete('version');
        params.delete('status');
        params.delete('timezone');
        router.push(`?${params.toString()}`);
    }

  return (
      <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
        <DialogTitle>Фильтры</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2}>
            <Typography variant="subtitle1">Поиск</Typography>
            <Search />

            <Typography variant="subtitle1">Версия</Typography>
            <VersionSelect />

            <Typography variant="subtitle1">Статус</Typography>
            <StatusSelect />

            <Typography variant="subtitle1">Часовой пояс</Typography>
            <TimezoneSelect />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button color='warning' onClick={clearModalFilters}>Сбросить</Button>
            <Tooltip title='При закрытии значения сохраняться'>
                <Button onClick={onClose} color="primary">Закрыть</Button>
            </Tooltip>
        </DialogActions>
      </Dialog>
  );
};

export default FiltersModal;