import { cn } from '@/utils/utils'
import Link from 'next/link'

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
			<Link className={cn('hover:text-blue-400')} href={`/nomenclatures/${client.id}`}>{client.name}</Link>
			{/* <span className="text-xl text-zinc-900">ID: {client.id}</span> */}
		</div>
	)
}
