interface OwnerInfoProps {
  owner: {
    full_name: string
  }
  className?: string
}

export const OwnerInfo = ({ owner, className }: OwnerInfoProps) => {
  
  return (
    <div className={`flex flex-col ${className}`}>
      <span className='font-semibold text-xl text-zinc-900'>{owner.full_name !== '' ? owner.full_name : 'N/D'}</span>
    </div>
  )
}
