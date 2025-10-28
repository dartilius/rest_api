'use client'

import {Alert, Box, Button, Modal, Snackbar, TextField, Typography} from "@mui/material";
import {ChangeEvent, useState} from "react";
import {handleResend, handleSendAction, handleSendCommand} from "../utils";

type ActionButtonsProps = {
    id: string;
};

export function ActionButtons({ id }: ActionButtonsProps) {
    const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    const [open, setOpen] = useState(false);
    const [openModal, setOpenModal] = useState<boolean>(false);
    const [command, setCommand] = useState<string>("");

    const handleClose = () => {
        setOpen(false);
    };
    const handleOpenModal = () => {
        setOpenModal(true);
    }

    const handleCloseModal = () => {
        setOpenModal(false);
    }

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
                    <Button onClick={handleOpenModal} color='error' variant='contained'>Выполнить bash команду</Button>
                </div>
            </div>
            {openModal && (
                <Modal
                    open={openModal}
                    onClose={handleCloseModal}
                    aria-labelledby="modal-modal-title"
                    aria-describedby="modal-modal-description"
                >
                    <Box sx={style}>
                        <Typography id="modal-modal-title" variant="h6" component="h2">
                            Введите sh команду
                        </Typography>
                        <TextField
                            variant="outlined"
                            fullWidth
                            onChange={(e: ChangeEvent<HTMLInputElement>) => {
                                setCommand(e.target.value);
                            }}
                            value={command}
                            style={{backgroundColor: 'white', borderRadius: '4px'}}
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <Button onClick={() => handleSendCommand(id, 'custom', setAlert, setOpen, command, handleCloseModal, setCommand)} variant="contained" color="info" style={{ maxWidth: '104px', justifyContent: 'center' }}>Выполнить</Button>
                        </div>
                    </Box>
                </Modal>
            )}
        </>
    );
}


const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 400,
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
    color: 'black',
    borderRadius: 4,
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
};