interface LabelProps {
	children: React.ReactNode
	className?: string
}

export const Label = ({ children, className }: LabelProps) => (
	<div
		className={`text-zinc-700 
    mb-1
    text-sm md:text-base  
    font-medium         
    leading-tight ${className}`}
	>
		{children}
	</div>
)
