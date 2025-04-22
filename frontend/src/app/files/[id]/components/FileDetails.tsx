'use client'

import { IFileDetailResponse } from '@/types/fileTypes'
import { Label } from '@/components/data-display/Label'
import { Name } from '@/components/data-display/Name'
import { DateTime } from '@/components/data-display/DateTime'
import { OwnerInfo } from '@/components/data-display/OwnerInfo'
import { Button } from '@mui/material'
import React from 'react'
import { useNotification } from '@/hooks/useNotification'
import dynamic from 'next/dynamic'
import { CopyButton } from '@/components/Ui/button/CoppyButton'

interface FileDetailsProps {
	data: IFileDetailResponse
	className?: string
}

const PreviewFile = dynamic(() => import('@/app/files/components/PreviewFile/PreviewFile'), {
	ssr: false,
})

function FileDetails({ data, className }: FileDetailsProps) {
	const { showNotification } = useNotification()

	const copyToClipboard = (text: string) => {
		navigator.clipboard
			.writeText(text)
			.then(() => showNotification('Hash скопирован!', 'success'))
			.catch((err) => showNotification('Не удалось скопировать Hash!', 'error'))
	}

	return (
		<div
			className={`bg-gradient-to-r from-cyan-600 to-blue-500 rounded-lg shadow p-4 md:p-6 ${className}`}
		>
			<div className='flex flex-col md:flex-row md:items-center md:justify-between gap-2 md:gap-4 mb-4 md:mb-6'>
				<div className='md:text-center w-full'>
					<Label className='text-sm md:text-base'>Название:</Label>
					<Name
						name={data.name}
						className='text-xl md:text-2xl break-words text-sky-200'
					/>
				</div>
			</div>
			<div className='grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6'>
				<div className='space-y-3 md:space-y-4'>
					<div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4 flex justify-center items-center'>
						<PreviewFile
							file={data}
							fileType={data.name}
						/>
					</div>
				</div>

				<div className='space-y-3 md:space-y-4'>
					<div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4'>
						<Label className='text-sm md:text-base'>Дата создания:</Label>
						<DateTime
							date={data.created}
							className='text-base md:text-lg text-zinc-900'
						/>
					</div>
					<div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4'>
						<Label className='text-sm md:text-base'>Владелец:</Label>
						<OwnerInfo
							owner={data.owner}
							className='text-base md:text-lg text-zinc-900'
						/>
					</div>
					<div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4'>
						<Label className='text-sm md:text-base'>Hash:</Label>
						<CopyButton
							onCopy={() => copyToClipboard(data.hash)}
							label={data.hash.slice(0, 20) + '...'}
						/>
					</div>
				</div>
			</div>
		</div>
	)
}

export default FileDetails
