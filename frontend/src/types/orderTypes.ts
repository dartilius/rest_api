import {
  MusicNote,
  Videocam,
  Image,
  TextFields,
  Schedule,
  LiveTv,
  CheckCircle,
  Cancel,
  Error,
} from '@mui/icons-material'
export interface IClient {
  id: string
  name: string
}
export interface IBroadcastInterval {
  lower: string
  upper: string
}
// Enum для типа фона
export enum BgOrderType {
  MUSIC = 0,
  VIDEO = 1,
  IMAGES = 2,
  TICKER = 3,
}
export enum BgOrderStatus {
  PENDING = 0,
  LIVE = 1,
  COMPLETED = 2,
  CANCELLED = 3,
  ERROR = 4,
}

import { SvgIconTypeMap } from '@mui/material'
import { OverridableComponent } from '@mui/material/OverridableComponent'

type IconType = OverridableComponent<SvgIconTypeMap<object, 'svg'>> & {
  muiName: string
}

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

export const ORDER_TYPE_CONFIG: Record<BgOrderType, TypeConfig> = {
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

export const STATUS_CONFIG: Record<BgOrderStatus, StatusConfig> = {
  [BgOrderStatus.PENDING]: {
    label: 'Ожидает эфира',
    icon: Schedule,
    className: 'text-amber-800',
    backgroundColor: 'rgba(255, 167, 86, 0.5)',
  },
  [BgOrderStatus.LIVE]: {
    label: 'В эфире',
    icon: LiveTv,
    className: 'text-green-800 animate-pulse',
    backgroundColor: 'rgba(0, 182, 155, 0.5)',
  },
  [BgOrderStatus.COMPLETED]: {
    label: 'Завершен',
    icon: CheckCircle,
    className: 'text-gray-800',
    backgroundColor: 'rgba(128, 128, 128, 0.5)',
  },
  [BgOrderStatus.CANCELLED]: {
    label: 'Отменен',
    icon: Cancel,
    className: 'text-red-800',
    backgroundColor: 'rgba(239, 56, 40, 0.5)',
  },
  [BgOrderStatus.ERROR]: {
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
  order_type: BgOrderType // Обязательное поле +
  playlist: { files_count: number; id: string; name: string } // Плейлист, обязательное поле +
  broadcast_interval: IBroadcastInterval // Обязательное поле +
  status: BgOrderStatus // Статус +
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
  owner: {
    full_name: string
  } // Создатель +
  playlist: { files_count: number; id: string; name: string } // Плейлист, обязательное поле +
  slides: any // TODO проверить что за тип
  broadcast_interval: IBroadcastInterval // Обязательное поле +
  parameters: {
    end_time: []
    times_in_hour: number
    weight: number
  }
  status: BgOrderStatus // Статус +
  created: string // Дата создания +
  client: IClient // Обязательное поле +
  // order_type: BgOrderType // Обязательное поле +
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
