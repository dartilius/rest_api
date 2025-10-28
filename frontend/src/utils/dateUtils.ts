import dayjs from 'dayjs'
import 'dayjs/locale/ru'

if (typeof window !== 'undefined') {
  dayjs.locale('ru')
}

export const formatDateTime = (dateString: string) => {
  return dayjs(dateString).format('DD.MM.YYYY HH:mm:ss')
}

export const formatTime = (timeString: string) => {
    // Добавим проверку валидности данных
    if (!timeString || typeof timeString !== 'string') return 'Н/Д'
    
    const [hours, minutes] = timeString.split(':')
    
    // Создаем Date объект с фиктивной датой, но правильным временем
    const date = dayjs()
      .set('hour', parseInt(hours))
      .set('minute', parseInt(minutes))
      .set('second', 0)
  
    return date.isValid() 
      ? date.format('HH:mm') 
      : 'Н/Д'
  }