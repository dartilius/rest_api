export const DAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const
export const DAY_LABELS: Record<string, string> = {
    mon: 'Пн',
    tue: 'Вт',
    wed: 'Ср',
    thu: 'Чт',
    fri: 'Пт',
    sat: 'Сб',
    sun: 'Вс',
}

export const defaultDaySettings = {
    worktime: '',
    default_volume: [0, 0, 0, 0],
} as const

export const defaultSettings = Object.fromEntries(
    DAY_KEYS.map((day) => [day, { ...defaultDaySettings }])
) as Record<typeof DAY_KEYS[number], typeof defaultDaySettings>