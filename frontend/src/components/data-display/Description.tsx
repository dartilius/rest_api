interface DescriptionProps {
  description: string
  className?: string
}

export const Description = ({ description, className }: DescriptionProps) => {
  return (
    <div className={`flex flex-col ${className}`}>
      <span className='font-semibold text-xl text-zinc-900'>
        {description !== '' ? description : 'N/D'}
      </span>
    </div>
  )
}
