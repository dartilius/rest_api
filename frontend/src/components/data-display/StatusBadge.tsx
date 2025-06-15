// components/StatusBadge.tsx
import { OrderStatus, STATUS_CONFIG } from '@/types/orderTypes'

interface StatusBadgeProps {
  status: OrderStatus
  className?: string
  iconClassName?: string
  size?: 'sm' | 'md' | 'lg'
}

const StatusBadge = ({
  status,
  className = '',
  iconClassName = 'w-4 h-4',
  size = 'md',
}: StatusBadgeProps) => {
  const {
    label,
    icon: Icon,
    backgroundColor,
  } = STATUS_CONFIG[status] || {
    label: 'Неизвестный статус',
    icon: Error,
    className: 'bg-gray-100 text-gray-800',
  }

  const sizeClasses = {
    sm: 'px-1 py-0.5 text-xs w-full',
    md: 'px-1 py-0.5 text-sm w-full',
    lg: 'px-2 py-1 text-base w-full',
  };

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

export default StatusBadge
