import {
  AccessTime,
  MusicNote,
  Videocam,
  Image,
  TextFields,
  Schedule,
  LiveTv,
  CheckCircle,
  Cancel,
  Error,
  AvTimer,
  TimerOff,
  HourglassTop,
  HourglassBottom,
  EventAvailable,
} from '@mui/icons-material'
import { SvgIconTypeMap } from '@mui/material'
import { OverridableComponent } from '@mui/material/OverridableComponent'

type IconType = OverridableComponent<SvgIconTypeMap<object, 'svg'>> & {
  muiName: string
}

export interface IClient {
  id: string
  name: string
}
export interface IBroadcastInterval {
  lower: string
  upper: string
}

export enum BgOrderType {
  MUSIC = 0,
  VIDEO = 1,
  IMAGES = 2,
  TICKER = 3,
}
export enum OrderStatus {
  PENDING = 0,
  LIVE = 1,
  COMPLETED = 2,
  CANCELLED = 3,
  ERROR = 4,
}
export enum AdOrderType{
  POINT_TIME = 0,
  START_OFFSET = 1,
  END_OFFSET = 2,
  SPECIFIC_HOURS = 3, // Новый тип
  OPEN_TO_HOUR = 4,
  FIXED_TO_CLOSE = 5,
  EVENT_START = 6,
}

export const ORDER_TYPE_AD_CONFIG: Record<AdOrderType, TypeConfig> = {
  [AdOrderType.POINT_TIME]: {
    label: 'По времени работы точки',
    icon: Schedule,
    className: 'bg-blue-100 text-blue-800',
  },
  [AdOrderType.START_OFFSET]: {
    label: 'Начало работы + смещение по времени',
    icon: AvTimer,
    className: 'bg-green-100 text-green-800',
  },
  [AdOrderType.END_OFFSET]: {
    label: 'Конец работы – смещение по времени',
    icon: TimerOff,
    className: 'bg-purple-100 text-purple-800',
  },
  [AdOrderType.SPECIFIC_HOURS]: { // Новый конфиг
    label: 'По конкретным часам',
    icon: AccessTime,
    className: 'bg-cyan-100 text-cyan-800',
  },
  [AdOrderType.OPEN_TO_HOUR]: {
    label: 'С открытия до конкретного часа',
    icon: HourglassTop,
    className: 'bg-orange-100 text-orange-800',
  },
  [AdOrderType.FIXED_TO_CLOSE]: {
    label: 'С фиксированного часа до закрытия',
    icon: HourglassBottom,
    className: 'bg-pink-100 text-pink-800',
  },
  [AdOrderType.EVENT_START]: {
    label: 'Старт по событию',
    icon: EventAvailable,
    className: 'bg-indigo-100 text-indigo-800',
  },
};
export interface TypeConfig {
  label: string
  icon: IconType
  className: string
}

export interface StatusConfig {
  label: string
  icon: IconType
  className: string
  backgroundColor: string
}

export const ORDER_TYPE_BG_CONFIG: Record<BgOrderType, TypeConfig> = {
  [BgOrderType.MUSIC]: {
    label: 'Музыка',
    icon: MusicNote,
    className: 'bg-blue-100 text-blue-800',
  },
  [BgOrderType.VIDEO]: {
    label: 'Видео',
    icon: Videocam,
    className: 'bg-green-100 text-green-800',
  },
  [BgOrderType.IMAGES]: {
    label: 'Картинки',
    icon: Image,
    className: 'bg-purple-100 text-purple-800',
  },
  [BgOrderType.TICKER]: {
    label: 'Бегущая строка',
    icon: TextFields,
    className: 'bg-orange-100 text-orange-800',
  },
}

export const STATUS_CONFIG: Record<OrderStatus, StatusConfig> = {
  [OrderStatus.PENDING]: {
    label: 'Ожидает эфира',
    icon: Schedule,
    className: 'text-amber-800',
    backgroundColor: 'rgba(255, 167, 86, 0.5)',
  },
  [OrderStatus.LIVE]: {
    label: 'В эфире',
    icon: LiveTv,
    className: 'text-green-800 animate-pulse',
    backgroundColor: 'rgba(0, 182, 155, 0.5)',
  },
  [OrderStatus.COMPLETED]: {
    label: 'Завершен',
    icon: CheckCircle,
    className: 'text-gray-800',
    backgroundColor: 'rgba(128, 128, 128, 0.5)',
  },
  [OrderStatus.CANCELLED]: {
    label: 'Отменён',
    icon: Cancel,
    className: 'text-red-800',
    backgroundColor: 'rgba(239, 56, 40, 0.5)',
  },
  [OrderStatus.ERROR]: {
    label: 'Ошибка',
    icon: Error,
    className: 'text-red-800',
    backgroundColor: 'rgba(239, 56, 40, 0.5)',
  },
}
export interface IBgData {
  id: string
  name: string
  client: IClient
  order_type: number
  status: number
  broadcast_interval: IBroadcastInterval
}
export interface IBgOrderDetail {
  id: string // Уникальный идентификатор +
  name: string // Название, обязательное поле, 1-255 символов +
  description: string | null // Описание +
  owner: {
    full_name: string
  } // Создатель +
  client: IClient // Обязательное поле +
  order_type: number // Обязательное поле +
  playlist: { files_count: number; id: string; name: string } // Плейлист, обязательное поле +
  broadcast_interval: IBroadcastInterval // Обязательное поле +
  status: OrderStatus // Статус +
  created: string // Дата создания +
  parameters: {
    daily_start_time: string
    daily_end_time: string
    times_in_hour: number
  }
}
export interface IAdData {
  id: string
  name: string
  client: IClient
  broadcast_type: number
  status: number
  broadcast_interval: IBroadcastInterval
}

export interface IAdOrderDetail {
  id: string // Уникальный идентификатор +
  name: string // Название, обязательное поле, 1-255 символов +
  description: string | null // Описание +
  broadcast_type: number
  owner: {
    full_name: string
  } // Создатель +
  playlist: { files_count: number; id: string; name: string } // Плейлист, обязательное поле +
  slides: any // TODO проверить что за тип
  broadcast_interval: IBroadcastInterval // Обязательное поле +
  parameters: {
    end_time: any
    timedelta: any
    start_time: any
    times_in_hour: number
    weight: number
  }
  status: OrderStatus // Статус +
  created: string // Дата создания +
  client: IClient // Обязательное поле +
}

export interface IDataBgResponse {
  count: number
  next: string | null
  previous: string | null
  results: IBgData[]
}

export interface IDataAdResponse {
  count: number
  next: string | null
  previous: string | null
  results: IAdData[]
}
