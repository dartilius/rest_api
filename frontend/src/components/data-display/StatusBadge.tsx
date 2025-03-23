// components/StatusBadge.tsx
import { BgOrderStatus, STATUS_CONFIG } from '@/types/orderTypes'

interface StatusBadgeProps {
  status: BgOrderStatus
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
    className: configClass,
    backgroundColor,
  } = STATUS_CONFIG[status] || {
    label: 'Неизвестный статус',
    icon: Error,
    className: 'bg-gray-100 text-gray-800',
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs min-w-[100px]',
    md: 'px-3 py-1 text-sm min-w-[160px]',
    lg: 'px-4 py-2 text-base min-w-[200px]'
  };

  return (
    <span
      style={{ backgroundColor: backgroundColor }}
      className={`inline-flex justify-center items-center gap-2 rounded-full ${sizeClasses[size]} ${configClass} ${className}`}
    >
      <Icon className={iconClassName} />
      {label}
    </span>
  )
}

export default StatusBadge
