'use client'

import { guessType } from '@/utils/convertTypeFile'
import Image from 'next/image'
import { SyntheticEvent, useState } from 'react'
import { IFileDetailResponse } from '@/types/fileTypes'

type PreviewFileProps = {
	file: IFileDetailResponse
	fileType: string
}

function PreviewFile({ file, fileType }: PreviewFileProps) {
	const [aspectRatio, setAspectRatio] = useState<string>('16 / 9')
	const [isVertical, setIsVertical] = useState(false);

	if (!file || !fileType) return null

	function handleLoadedMetadata(e: SyntheticEvent<HTMLVideoElement>) {
		const video = e.currentTarget;
		const width = video.videoWidth;
		const height = video.videoHeight;

		if (width && height) {
			setAspectRatio(`${width} / ${height}`);
			setIsVertical(height > width);
		}
	}

	const type = guessType(fileType)

	switch (type) {
		case 'image':
			return (
				<Image
					src={file.url}
					alt={file.name}
					width={480}
					height={480}
					style={{ borderRadius: '8px', objectFit: 'cover' }}
				/>
			)
		case 'video':
			return (
				<div
					style={{
						position: 'relative',
						width: isVertical ? '300px' : '100%',
						maxWidth: '640px',
						aspectRatio,
						maxHeight: '80vh',
						overflow: 'hidden',
						borderRadius: '8px',
					}}
				>
					<video
						controls
						src={file.url}
						onLoadedMetadata={handleLoadedMetadata}
						style={{
							width: '100%',
							height: '100%',
							objectFit: 'cover',
						}}
					>
						Ваш браузер не поддерживает видео.
					</video>
				</div>
			)
		case 'audio':
			return (
				<audio controls>
					<source
						src={file.url}
						type='audio/mpeg'
					/>
					Ваш браузер не поддерживает аудио.
				</audio>
			)
		default:
			return <strong>Предпросмотр недоступен</strong>
	}
}

export default PreviewFile
