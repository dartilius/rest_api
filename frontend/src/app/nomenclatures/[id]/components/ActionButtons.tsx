'use client'

import { Alert, Button, Snackbar } from "@mui/material";
import { useState } from "react";
import {handleResend, handleSendAction} from "@/app/nomenclatures/[id]/lib";

type ActionButtonsProps = {
    id: string;
};

export function ActionButtons({ id }: ActionButtonsProps) {
    const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    const [open, setOpen] = useState(false);

    const handleClose = () => {
        setOpen(false);
    };

    return (
        <>
            <Snackbar
                open={open}
                autoHideDuration={3000}
                onClose={handleClose}
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                {alert ? (
                    <Alert
                        variant="filled"
                        severity={alert.type}
                        onClose={handleClose}
                        sx={{
                            transition: 'opacity 0.3s ease-in-out',
                        }}
                    >
                        {alert.message}
                    </Alert>
                ) : <div></div>}
            </Snackbar>

            <div style={{display: 'flex', gap: '1rem', flexDirection: 'column'}}>
                <div style={{display: 'flex', gap: '1rem', flexDirection: 'column'}}>
                    <Button onClick={() => handleResend(id, setAlert, setOpen)} color='secondary' variant='contained' style={{width: '100%'}}>Переотправка заказов</Button>
                    <Button onClick={() => handleSendAction(id, 'update', setAlert, setOpen)} color='info' variant='contained' style={{width: '100%'}}>Обновить</Button>
                    <Button onClick={() => handleSendAction(id, 'reboot', setAlert, setOpen)} color='warning' variant='contained' style={{ width: '100%'}}>Перезапустить</Button>
                </div>
            </div>
        </>
    );
}
