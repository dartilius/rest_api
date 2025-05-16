'use client'

import { cn } from '@/utils/utils'
import { ComponentType, MouseEvent, ReactNode } from 'react'

interface ActionButtonProps {
	variant?: 'primary' | 'secondary' | 'error' | 'transparent' | 'warning'
	size?: 'sm' | 'md' | 'lg'
	className?: string
	icon?: ComponentType<{ className?: string }>
	iconClassName?: string
	onClick?: (e?: MouseEvent) => void
	children: ReactNode
	disabled?: boolean
	type?: 'button' | 'submit' | 'reset'
	style?: React.CSSProperties
}

const BUTTON_CONFIG = {
	primary: 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl active:shadow-inner',
	secondary:
		'bg-gray-100 text-gray-900 hover:bg-gray-200 shadow-md hover:shadow-lg active:shadow-inner',
	error: 'bg-red-600 text-white hover:bg-red-700 shadow-lg hover:shadow-xl active:shadow-inner',
	warning:
		'bg-amber-500 text-white hover:bg-amber-600 shadow-md hover:shadow-lg active:shadow-inner',
	transparent: 'bg-transparent text-gray-900 hover:bg-gray-100',
}

const SIZE_CLASSES = {
	sm: 'px-3 py-1 text-sm gap-1',
	md: 'px-4 py-2 text-base gap-2',
	lg: 'px-5 py-3 text-lg gap-3',
}

const ActionButton = ({
	variant = 'primary',
	size = 'md',
	className = '',
	icon: Icon,
	iconClassName = 'w-5 h-5',
	onClick,
	children,
	disabled = false,
	type = 'button',
	style,
}: ActionButtonProps) => {
	return (
		<button
			type={type}
			onClick={onClick}
			disabled={disabled}
			style={style}
			className={cn(
				'inline-flex items-center rounded-full transition-all',
				'duration-200 ease-out transform',
				'hover:-translate-y-0.5 active:translate-y-0',
				'active:scale-95 hover:outline-1 hover:ring-2 hover:ring-offset-2',
				BUTTON_CONFIG[variant],
				SIZE_CLASSES[size],
				disabled && 'opacity-50 cursor-not-allowed',
				variant !== 'transparent' && 'focus:ring-current',
				className,
			)}
		>
			{Icon && <Icon className={iconClassName} />}
			{children}
		</button>
	)
}

export default ActionButton
