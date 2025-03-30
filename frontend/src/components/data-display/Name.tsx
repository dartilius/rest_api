interface NameProps {
  name: string
  className?: string
}

export const Name = ({ name, className }: NameProps) => {
  return (
    <div className={`flex flex-col ${className}`}>
      <span className='font-semibold uppercase'>
        {name !== '' ? name : 'N/D'}
      </span>
    </div>
  )
}
