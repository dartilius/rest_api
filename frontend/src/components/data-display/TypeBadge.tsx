import {
  AdOrderType,
  BgOrderType,
  ORDER_TYPE_AD_CONFIG,
  ORDER_TYPE_BG_CONFIG,
} from '@/types/orderTypes'

interface TypeBadgeProps {
  type: BgOrderType | AdOrderType
  className?: string
  iconClassName?: string
  size?: 'sm' | 'md' | 'lg'
  mode?: 'bg' | 'ad' // Новый проп для определения типа конфига
}

const TypeBadge = ({
  type,
  className = '',
  iconClassName = 'w-4 h-4',
  size = 'md',
  mode = 'bg', // Значение по умолчанию
}: TypeBadgeProps) => {
  // Выбираем конфиг в зависимости от режима
  const config =
    mode === 'bg'
      ? ORDER_TYPE_BG_CONFIG[type as BgOrderType]
      : ORDER_TYPE_AD_CONFIG[type as AdOrderType]

  const {
    label,
    icon: Icon,
    backgroundColor,
  } = config || {
    label: 'Неизвестный тип',
    icon: Error,
    className: 'bg-gray-100 text-gray-800',
  }

  const sizeClasses = {
    sm: 'px-1 py-0.5 text-xs w-full',
    md: 'px-1 py-0.5 text-sm w-full',
    lg: 'px-2 py-1 text-base w-full',
  }
  console.log(type)

  return (
    <span
    style={{ backgroundColor: backgroundColor }}
      className={`inline-flex justify-center items-center gap-2 rounded-full ${sizeClasses[size]} ${className}`}
    >
      <Icon className={iconClassName} />
      {label}
    </span>
  )
}

export default TypeBadge
