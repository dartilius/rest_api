import Link from 'next/link'
import { Label } from './Label'
import { cn } from '@/utils/utils'

interface PlaylistInfoProps {
	playlist: Array<{
		id: string
		name: string
		files_count?: number
		url?: string
	}>
	files_count?: number
	className?: string
}

export const PlaylistInfo = ({ playlist, files_count, className }: PlaylistInfoProps) => {
	console.log(playlist)

	return (
		<div className={`flex flex-col gap-3 ${className}`}>
			{files_count && (
				<div className='mb-2'>
					<Label>Файлов в плейлисте:</Label>
					<span className='font-semibold text-zinc-900'>{files_count}</span>
				</div>
			)}

			<div className='flex flex-col gap-2'>
				{playlist.map((file) => (
					<div
						key={file.id}
						className='flex flex-col items-center'
					>
						<div className='w-full min-w-0'>
							{file.url ? (
								<a
									href={file.url}
									target='_blank'
									rel='noopener noreferrer'
									className='
                    font-medium 
                    hover:underline 
                    break-words
                    whitespace-normal
                    overflow-hidden 
                    block 
                    w-full
                  '
								>
									{file.name}
								</a>
							) : (
								/** данный элемент отображается в бг и ад расшифровке */
								/** он кликабелен для перехода в плейлист */
								<Link
									href={`/playlists/${file.id}`}
									className='w-full min-w-0'
								>
									<span
										className={cn(
											'font-medium',
											'  text-blue-100',
											' hover:text-blue-800 ',
											' transition-colors ',
											'duration-200 ',
											'break-words ',
											' whitespace-normal',
											'relative',
											' after:content-[""]',
											'  after:absolute',
											'  after:bottom-0',
											' after:left-0',
											'after:w-0',
											'after:h-px',
											' after:bg-blue-600',
											'group-hover:after:w-full',
											'after:transition-all',
											'after:duration-300',
										)}
									>
										{file.name}
									</span>
								</Link>
							)}
						</div>

						{file.files_count && (
							<div className='w-full'>
								<span className='text-start text-base md:text-2xl text-zinc-900'>
									Вложенных файлов: {file.files_count}
								</span>
							</div>
						)}
					</div>
				))}
			</div>
		</div>
	)
}
