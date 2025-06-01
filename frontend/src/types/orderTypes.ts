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
  SPECIFIC_HOURS = 3, 
  OPEN_TO_HOUR = 4,
  FIXED_TO_CLOSE = 5,
  EVENT_START = 6,
}

export const ORDER_TYPE_AD_CONFIG: Record<AdOrderType, TypeConfig> = {
  [AdOrderType.POINT_TIME]: {
    label: 'По времени работы точки',
    icon: Schedule,
    backgroundColor: 'rgba(173, 216, 230, 0.5)', // bg-blue-100
    textColor: 'rgba(0, 0, 139, 1)', // text-blue-800
  },
  [AdOrderType.START_OFFSET]: {
    label: 'Начало работы + смещение по времени',
    icon: AvTimer,
    backgroundColor: 'rgba(144, 238, 144, 0.5)', // bg-green-100
    textColor: 'rgba(0, 100, 0, 1)', // text-green-800
  },
  [AdOrderType.END_OFFSET]: {
    label: 'Конец работы – смещение по времени',
    icon: TimerOff,
    backgroundColor: 'rgba(221, 160, 221, 0.5)', // bg-purple-100
    textColor: 'rgba(128, 0, 128, 1)', // text-purple-800
  },
  [AdOrderType.SPECIFIC_HOURS]: { // Новый конфиг
    label: 'По конкретным часам',
    icon: AccessTime,
    backgroundColor: 'rgba(135, 206, 235, 0.5)', // bg-cyan-100
    textColor: 'rgba(0, 139, 139, 1)', // text-cyan-800
  },
  [AdOrderType.OPEN_TO_HOUR]: {
    label: 'С открытия до конкретного часа',
    icon: HourglassTop,
    backgroundColor: 'rgba(255, 165, 0, 0.5)', // bg-orange-100
    textColor: 'rgba(255, 69, 0, 1)', // text-orange-800
  },
  [AdOrderType.FIXED_TO_CLOSE]: {
    label: 'С фиксированного часа до закрытия',
    icon: HourglassBottom,
    backgroundColor: 'rgba(255, 192, 203, 0.5)', // bg-pink-100
    textColor: 'rgba(219, 112, 147, 1)', // text-pink-800
  },
  [AdOrderType.EVENT_START]: {
    label: 'Старт по событию',
    icon: EventAvailable,
    backgroundColor: 'rgba(100, 149, 237, 0.5)', // bg-indigo-100
    textColor: 'rgba(75, 0, 130, 1)', // text-indigo-800
  },
};

export interface TypeConfig {
  label: string
  icon: IconType
  backgroundColor: string
  textColor?: string
}

export interface StatusConfig {
  label: string
  icon: IconType
  textColor: string
  backgroundColor: string
}

export const ORDER_TYPE_BG_CONFIG: Record<BgOrderType, TypeConfig> = {
  [BgOrderType.MUSIC]: {
    label: 'Музыка',
    icon: MusicNote,
    backgroundColor: 'rgba(219, 234, 254, 0.1)', // bg-blue-100
    textColor: 'rgba(0, 0, 139, 1)', // text-blue-800
  },
  [BgOrderType.VIDEO]: {
    label: 'Видео',
    icon: Videocam,
    backgroundColor: 'rgba(220, 252, 231, 0.1)', // bg-green-100
    textColor: 'rgba(0, 100, 0, 1)', // text-green-800
  },
  [BgOrderType.IMAGES]: {
    label: 'Картинки',
    icon: Image,
    backgroundColor: 'rgba(233, 213, 255, 0.1)', // bg-purple-100
    textColor: 'rgba(128, 0, 128, 1)', // text-purple-800
  },
  [BgOrderType.TICKER]: {
    label: 'Бегущая строка',
    icon: TextFields,
    backgroundColor: 'rgba(255, 237, 213, 0.1)', // bg-orange-100
    textColor: 'rgba(255, 69, 0, 1)', // text-orange-800
  },
};


export const STATUS_CONFIG: Record<OrderStatus, StatusConfig> = {
  [OrderStatus.PENDING]: {
    label: 'Ожидает эфира',
    icon: Schedule,
    textColor: 'rgba(255, 121, 28, 1)', // text-amber-800
    backgroundColor: 'rgba(255, 167, 86, 0.5)',
  },
  [OrderStatus.LIVE]: {
    label: 'В эфире',
    icon: LiveTv,
    textColor: 'rgba(0, 100, 0, 1) animate-pulse', // text-green-800
    backgroundColor: 'rgba(0, 182, 155, 0.5)',
  },
  [OrderStatus.COMPLETED]: {
    label: 'Завершен',
    icon: CheckCircle,
    textColor: 'rgba(75, 85, 99, 1)', // text-gray-800
    backgroundColor: 'rgba(128, 128, 128, 0.5)',
  },
  [OrderStatus.CANCELLED]: {
    label: 'Отменён',
    icon: Cancel,
    textColor: 'rgba(239, 56, 40, 1)', // text-red-800
    backgroundColor: 'rgba(239, 56, 40, 0.5)',
  },
  [OrderStatus.ERROR]: {
    label: 'Ошибка',
    icon: Error,
    textColor: 'rgba(239, 56, 40, 1)', // text-red-800
    backgroundColor: 'rgba(239, 56, 40, 0.5)',
  },
};

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

export interface IParamsCreateAd {
  weight: number;
  times_in_hour: number;
  timedelta?: string;
  start_time?: string;
  end_time?: string;
  event?: string;
  active_ad?: string;
}
export interface IParamsCreateBg {
  weight: number;
  times_in_hour: number;
  timedelta?: string;
  start_time?: string;
  end_time?: string;
  event?: string;
  active_ad?: string;
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

  results: IBgData[]
}

export interface IDataAdResponse {
  count: number
  results: IAdData[]
}
