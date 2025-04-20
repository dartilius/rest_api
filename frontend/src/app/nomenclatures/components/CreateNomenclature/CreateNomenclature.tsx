'use client'

import { ChangeEvent, useState } from 'react'
import {
    Dialog,
    DialogContent,
    DialogTitle,
    Typography,
    useMediaQuery,
    useTheme,
    TextField,
    Grid,
    Button,
    DialogActions
} from '@mui/material'

import { ICreateNomenclature } from '@/types/nomeclaturesType'
import { createNomenclature } from '@/services/NomenclaturesService'
import { useRouter } from 'next/navigation'
import { useNotification } from '@/hooks/useNotification'
import styles from '@/app/nomenclatures/Nomenclatures.module.scss'

const DAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const
const DAY_LABELS: Record<string, string> = {
    mon: 'Пн',
    tue: 'Вт',
    wed: 'Ср',
    thu: 'Чт',
    fri: 'Пт',
    sat: 'Сб',
    sun: 'Вс',
}

const defaultDaySettings: ICreateNomenclature['settings'][keyof ICreateNomenclature['settings']] = {
    worktime: '',
    default_volume: [0,0,0,0],
}

const defaultSettings: ICreateNomenclature['settings'] = Object.fromEntries(
    DAY_KEYS.map((day: any) => [day, { ...defaultDaySettings }])
) as ICreateNomenclature['settings']

const isValidWorktime = (value: string): boolean => {
    const regex = /^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$/
    return regex.test(value)
}

const isValidVolume = (arr: number[]): boolean => {
    return arr.length === 4 && arr.every(v => !isNaN(v) && v >= 0 && v <= 100)
}

function CreateNomenclature() {
    const [open, setOpen] = useState<boolean>(false)
    const router = useRouter()

    const [formState, setFormState] = useState<ICreateNomenclature>({
        name: '',
        description: '',
        version: '',
        settings: defaultSettings
    })

    const [formErrors, setFormErrors] = useState<Record<string, string>>({})

    const theme = useTheme()
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
    const { showNotification } = useNotification()

    const handleTextChange = (field: keyof Omit<ICreateNomenclature, 'settings'>) => (e: ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.slice(0, 250)
        setFormState((prev) => ({ ...prev, [field]: value }))
    }

    /*
    TODO: переписать код от чата
    const handleDaySettingChange = (
        day: keyof ICreateNomenclature['settings'],
        key: keyof ICreateNomenclature['settings'][keyof ICreateNomenclature['settings']]
    ) => (e: ChangeEvent<HTMLInputElement>) => {
        let value = e.target.value

        if (key === 'worktime') {
            // Оставляем только цифры
            const digits = value.replace(/\D/g, '').slice(0, 8)

            let formatted = ''
            if (digits.length >= 4) {
                formatted = `${digits.slice(0, 2)}:${digits.slice(2, 4)}`
            } else if (digits.length >= 2) {
                formatted = `${digits.slice(0, 2)}:${digits.slice(2)}`
            } else {
                formatted = digits
            }

            if (digits.length >= 8) {
                formatted += `-${digits.slice(4, 6)}:${digits.slice(6, 8)}`
            } else if (digits.length > 4) {
                formatted += `-${digits.slice(4)}`
            }

            setFormState((prev) => ({
                ...prev,
                settings: {
                    ...prev.settings,
                    [day]: {
                        ...prev.settings[day],
                        worktime: formatted
                    }
                }
            }))
        }

        if (key === 'default_volume') {
            const values = value
                .replace(/\s/g, '') // убираем пробелы
                .split(',')
                .map((v) => parseInt(v, 10))
                .filter((v) => !isNaN(v) && v >= 0 && v <= 100)
                .slice(0, 4)

            // Дополняем массив до 4 элементов
            while (values.length < 4) {
                values.push(0)
            }

            setFormState((prev) => ({
                ...prev,
                settings: {
                    ...prev.settings,
                    [day]: {
                        ...prev.settings[day],
                        default_volume: values as [number, number, number, number]
                    }
                }
            }))
        }

    }*/



    const handleSubmit = async () => {
        const errors: Record<string, string> = {}

        for (const day of DAY_KEYS) {
            const worktime = formState.settings[day].worktime
            const volume = formState.settings[day].default_volume

            if (!isValidWorktime(worktime)) {
                errors[`${day}-worktime`] = 'Неверный формат (должен быть HH:MM-HH:MM)'
            }

            if (!isValidVolume(volume)) {
                errors[`${day}-volume`] = 'Введите 4 числа от 0 до 100 через запятую'
            }
        }

        if (Object.keys(errors).length > 0) {
            setFormErrors(errors)
            return
        }

        try {
            await createNomenclature(formState)
            setFormState({
                name: '',
                description: '',
                version: '',
                settings: defaultSettings
            })
            setFormErrors({})
            setOpen(false)
            router.refresh()
            showNotification(`Номенклатура успешно создана`, 'success')
        } catch (error) {
            console.error('Ошибка создания:', error)
            showNotification(`Ошибка создания: ${error}`, 'error')
        }
    }

    return (
        <div>
            <button onClick={() => setOpen(true)}>Add new nomenclature</button>
            <Dialog
                open={open}
                onClose={() => setOpen(false)}
                fullScreen={isMobile}
                maxWidth='md'
                fullWidth
            >
                <DialogTitle>Создание новой номенклатуры</DialogTitle>

                <DialogContent dividers className={styles.custom_scroll}>
                    <TextField
                        label='Название'
                        type='text'
                        fullWidth
                        margin='dense'
                        value={formState.name}
                        onChange={handleTextChange('name')}
                        inputProps={{ maxLength: 250 }}
                    />
                    <Typography variant='caption' sx={{ display: 'block', textAlign: 'right', mt: -1 }}>
                        {formState.name.length}/250
                    </Typography>

                    <TextField
                        label='Описание'
                        type='text'
                        fullWidth
                        margin='dense'
                        value={formState.description}
                        onChange={handleTextChange('description')}
                        inputProps={{ maxLength: 250 }}
                    />
                    <Typography variant='caption' sx={{ display: 'block', textAlign: 'right', mt: -1 }}>
                        {formState.description.length}/250
                    </Typography>

                    <TextField
                        label='Версия'
                        type='text'
                        fullWidth
                        margin='dense'
                        value={formState.version}
                        onChange={handleTextChange('version')}
                        inputProps={{ maxLength: 250 }}
                    />

                    <Typography variant='h6' sx={{ mt: 2, mb: 1 }}>
                        Настройки по дням недели
                    </Typography>

                    {/*<Grid container spacing={2}>*/}
                    {/*    {DAY_KEYS.map((day: any) => (*/}
                    {/*        <Grid item xs={12} md={6} key={day}>*/}
                    {/*            <Typography variant='subtitle1' sx={{ mb: 1 }}>*/}
                    {/*                {DAY_LABELS[day]}*/}
                    {/*            </Typography>*/}

                    {/*            <TextField*/}
                    {/*                label='Рабочее время'*/}
                    {/*                fullWidth*/}
                    {/*                margin='dense'*/}
                    {/*                value={formState.settings[day].worktime}*/}
                    {/*                onChange={handleDaySettingChange(day, 'worktime')}*/}
                    {/*                error={!!formErrors[`${day}-worktime`]}*/}
                    {/*                helperText={formErrors[`${day}-worktime`] || ''}*/}
                    {/*            />*/}

                    {/*            <TextField*/}
                    {/*                label='Громкость по умолчанию (4 числа через запятую)'*/}
                    {/*                fullWidth*/}
                    {/*                margin='dense'*/}
                    {/*                value={formState.settings[day].default_volume.join(',')}*/}
                    {/*                onChange={handleDaySettingChange(day, 'default_volume')}*/}
                    {/*                error={!!formErrors[`${day}-volume`]}*/}
                    {/*                helperText={formErrors[`${day}-volume`] || ''}*/}
                    {/*            />*/}
                    {/*        </Grid>*/}
                    {/*    ))}*/}
                    {/*</Grid>*/}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpen(false)}>Отмена</Button>
                    <Button
                        variant='contained'
                        onClick={handleSubmit}
                        disabled={!formState.name}
                    >
                        Создать
                    </Button>
                </DialogActions>
            </Dialog>
        </div>
    )
}

export default CreateNomenclature


//TODO: Вместо ввода громкости сделать 4 селекта (Реклама: лево-право, Музыка: лево-право)