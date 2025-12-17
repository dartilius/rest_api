interface NameProps {
	name: string
	className?: string
}

export const Name = ({ name, className }: NameProps) => {
	return (
		<div className={`flex flex-col ${className}`}>
			<span className='text-sm md:text-lg uppercase font-semibold whitespace-nowrap'>
				{name !== '' ? name : 'N/D'}
			</span>
		</div>
	)
}
