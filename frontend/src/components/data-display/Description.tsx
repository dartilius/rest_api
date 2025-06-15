interface DescriptionProps {
	description: string
	className?: string
}

export const Description = ({ description, className }: DescriptionProps) => {
	return (
		<div className={`flex flex-col ${className}`}>
			<span className='font-semibold text-sm md:text-base whitespace-nowrap'>
				{description !== '' ? description : 'N/D'}
			</span>
		</div>
	)
}
