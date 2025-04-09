'use client'

import { guessType } from '@/utils/convertTypeFile'
import Image from 'next/image'
import { SyntheticEvent, useState } from 'react'
import { IFileDetailResponse } from '@/types/fileTypes'
import styles from './PreviewFile.module.scss' // SCSS файл для стилизации скелетона

type PreviewFileProps = {
	file: IFileDetailResponse
	fileType: string
	loading: boolean
}

function PreviewFile({ file, fileType, loading }: PreviewFileProps) {
	const [aspectRatio, setAspectRatio] = useState<string>('16 / 9')
	const [isVertical, setIsVertical] = useState(false)
	const [isLoaded, setIsLoaded] = useState(false)

	if (!file || !fileType) return null

	function handleLoadedMetadata(e: SyntheticEvent<HTMLVideoElement>) {
		const video = e.currentTarget
		const width = video.videoWidth
		const height = video.videoHeight

		if (width && height) {
			setAspectRatio(`${width} / ${height}`)
			setIsVertical(height > width)
		}
		setIsLoaded(true)
	}

	const type = guessType(fileType)

	switch (type) {
		case 'image':
			return (
				<div className={styles.previewWrapper}>
					{!isLoaded && <div className={styles.skeleton} />}
					<Image
						src={file.url}
						alt={file.name}
						width={480}
						height={480}
						loading="lazy"
						onLoad={() => setIsLoaded(true)}
						style={{
							borderRadius: '8px',
						}}
					/>
				</div>
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
					{!isLoaded && <div className={styles.skeleton} />}
					<video
						controls
						src={file.url}
						onLoadedMetadata={handleLoadedMetadata}
						style={{
							width: '100%',
							height: '100%',
							objectFit: 'cover',
							display: isLoaded ? 'block' : 'none',
						}}
					>
						Ваш браузер не поддерживает видео.
					</video>
				</div>
			)
		case 'audio':
			return (
				<audio controls>
					<source src={file.url} type="audio/mpeg" />
					Ваш браузер не поддерживает аудио.
				</audio>
			)
		default:
			return <strong>Предпросмотр недоступен</strong>
	}
}

export default PreviewFile
