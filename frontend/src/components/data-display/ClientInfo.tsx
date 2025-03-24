interface ClientInfoProps {
    client: {
      id: string
      name: string
    }
    className?: string
  }
  
  export const ClientInfo = ({ client, className }: ClientInfoProps) => {
    return (
      <div className={`flex flex-col ${className}`}>
        <span className="font-semibold">{client.name}</span>
        <span className="text-xl text-zinc-900">ID: {client.id}</span>
      </div>
    )
  }