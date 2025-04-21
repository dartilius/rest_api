import {Grid, Typography} from "@mui/material";
import ActionButton from "@/components/Ui/button/ActionButton";
import {ReactNode} from "react";

export const DaySettingsHeader = ({ onCopyMondaySettings }: { onCopyMondaySettings: () => void }) => (
    <>
        <Typography variant='h6' sx={{ mt: 2, mb: 1 }}>
            Настройки по дням недели
        </Typography>
        <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
            <ActionButton
                variant='primary'
                onClick={onCopyMondaySettings}
                className='mb-4'
            >
                Скопировать настройки с понедельника
            </ActionButton>
        </div>
    </>
)

export const DaySettingsGrid = ({ children }: { children: ReactNode }) => (
    <Grid container spacing={2} justifyContent='center'>
        {children}
    </Grid>
)