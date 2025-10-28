interface LabelProps {
	children: React.ReactNode
	className?: string
}

export const Label = ({ children, className }: LabelProps) => (
	<div className={`text-zinc-700 mb-1 ${className}`}>{children}</div>
)
