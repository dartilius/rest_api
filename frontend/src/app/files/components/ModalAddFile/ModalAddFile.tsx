"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import {Modal, Box, Button, Alert, Snackbar, Select, MenuItem, FormControl} from "@mui/material";
import "./ModalAddFile.scss";
import {ChangeEvent, useState} from "react";
import {sendFile} from "@/services/FilesService";
import {convertTypeForSendFile} from "@/utils/convertTypeFile";
function convertBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const fileReader = new FileReader();
        fileReader.readAsDataURL(file);

        fileReader.onload = () => {
            if (typeof fileReader.result === "string") {
                // Заменяем MIME-тип на имя файла
                const base64String = fileReader.result.replace(
                    /^data:[^;]+/,
                    `data:${file.name}`
                );
                resolve(base64String);
            } else {
                reject("Ошибка при чтении файла");
            }
        };

        fileReader.onerror = (error) => {
            reject(error);
        };
    });
}

const arrayOfTypesFile = [
    { id: 'image', label: 'Изображение' },
    { id: 'music', label: 'Музыка' },
    { id: 'video', label: 'Видео' },
    { id: 'ticker', label: 'Бегущая строка' },
    { id: 'ad', label: 'Реклама' }
];

export function ModalAddFile() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();
    const [fileName, setFileName] = useState<string>("Файл не выбран");
    const [fileBase64, setFileBase64] = useState<string>("");
    const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    const [openAlert, setOpenAlert] = useState(false);
    const [convertedType, setConvertedType] = useState<number | string>('');

    const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;
        try {
            const base64 = await convertBase64(file);
            setFileBase64(base64);
            setFileName(file.name);
        } catch (error) {
            setOpenAlert(true);
            setAlert({ type: 'error', message: String(error) });
            console.error("Ошибка при обработке файла:", error);
        }
    };


    const isOpen = searchParams.get("modal") === "open";

    const handleOpen = () => {
        const newUrl = `${pathname}?page=1&limit=12&modal=open`;
        router.push(newUrl, { scroll: false });
    };

    const handleClose = () => {
        const newUrl = `${pathname}?page=1&limit=12`;
        router.push(newUrl, { scroll: false });
    };
    const handleCloseAlert = () => {
        setOpenAlert(false);
    };

    const handleSelectTypeFile = (selectedType: string) => {
        console.log('selectedType', convertedType);
        setConvertedType(convertTypeForSendFile(selectedType))
    }

    const handleSendFile = async () => {
        if (!fileBase64) {
            setOpenAlert(true);
            setAlert({ type: 'error', message: "Файл не выбран" });
            return;
        }

        try {
            console.log(convertedType)
            const response = await sendFile({ source: fileBase64, type:  Number(convertedType)});
            console.log("Файл успешно отправлен:", response);

            setOpenAlert(true);
            setAlert({
                type: 'success',
                message: typeof response !== "string"
                    ? `Файл: ${response.name}, успешно создан`
                    : "Файл успешно создан"
            });
            handleClose()
        } catch (error: any) {
            setOpenAlert(true);
            setAlert({ type: 'error', message: error.message || "Неизвестная ошибка" });
            console.error("Ошибка при отправке файла:", error);
        }
    };




    return (
        <div>
            <Snackbar
                open={openAlert}
                autoHideDuration={3000}
                onClose={handleCloseAlert}
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
            <Button variant="contained" onClick={handleOpen} style={{maxHeight: '52px'}}>
                Открыть модальное окно
            </Button>

            <Modal open={isOpen} onClose={handleClose}>
                <Box sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 400,
                    bgcolor: 'background.paper',
                    boxShadow: 24,
                    p: 4,
                    borderRadius: 2,
                    color: 'black'
                }}>
                    <div style={{
                        display: "flex",
                        justifyContent: "space-between",
                        flexDirection: "column",
                        alignItems: "center"
                    }}>
                        <input type="file" name="file" id="file" className="inputfile inputfile-1" onChange={handleFileChange} />
                        <label htmlFor="file">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="17" viewBox="0 0 20 17">
                                <path
                                    d="M10 0l-5.2 4.9h3.3v5.1h3.8v-5.1h3.3l-5.2-4.9zm9.3 11.5l-3.2-2.1h-2l3.4 2.6h-3.5c-.1 0-.2.1-.2.1l-.8 2.3h-6l-.8-2.2c-.1-.1-.1-.2-.2-.2h-3.6l3.4-2.6h-2l-3.2 2.1c-.4.3-.7 1-.6 1.5l.6 3.1c.1.5.7.9 1.2.9h16.3c.6 0 1.1-.4 1.3-.9l.6-3.1c.1-.5-.2-1.2-.7-1.5z"/>
                            </svg>
                            Добавить файл&hellip;
                        </label>
                        {fileName}
                    </div>
                    <FormControl fullWidth>
                        <Select
                            onChange={(event) => {
                                const selectedType = event.target.value as string;
                                handleSelectTypeFile(selectedType);
                                setConvertedType(convertTypeForSendFile(selectedType));
                            }}
                            style={{ color: 'black', backgroundColor: 'white', borderRadius: '4px' }}
                        >
                            {arrayOfTypesFile.map((item) => (
                                <MenuItem key={item.id} value={item.id}>
                                    {item.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                    <div style={{display: "flex", justifyContent: 'space-between'}}>
                        <Button variant="outlined" onClick={handleClose} sx={{mt: 2}}>
                            Закрыть
                        </Button>
                        <Button variant="outlined" onClick={handleSendFile} sx={{ mt: 2 }}>
                            Отправить
                        </Button>
                    </div>
                </Box>
            </Modal>
        </div>
    );
}
