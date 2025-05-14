interface LabelProps {
	children: React.ReactNode
	className?: string
}

export const Label = ({ children, className }: LabelProps) => (
	<div className={`text-xl md:text-2xl text-zinc-700 mb-1 ${className}`}>{children}</div>
)
