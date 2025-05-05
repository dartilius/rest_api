import React, { useEffect, useState } from 'react'
import { Box, Button, Modal } from '@mui/material'
import CancelIcon from '@mui/icons-material/Cancel'
import { ITagResponse } from '@/types/fileTypes'
import SelectTags from '@/app/files/components/SelectTags/SelectTags'
import { useRouter } from 'next/navigation'
import { addTags, removeTags } from '../../api'

type ModalAddFileProps = {
	isOpen: boolean
	name: string
	tags: Array<ITagResponse>
	handleClose: () => void
	id: string
}

function ModalEditFile({ tags, name, isOpen, handleClose, id }: ModalAddFileProps) {
	const [localTags, setLocalTags] = useState<ITagResponse[]>(tags)
	const router = useRouter()

	useEffect(() => {
		if (isOpen) {
			setLocalTags(tags)
		}
	}, [isOpen, tags])

	const handleDeleteTag = (tagDelete: string) => {
		setLocalTags((prevTags) => prevTags.filter((tag) => tag.id !== tagDelete))
	}

	const handleSaveEdit = async () => {
		const initialIds = tags.map((t) => t.name)
		const updatedIds = localTags.map((t) => t.name)

		const tagsToAdd = updatedIds.filter((name) => !initialIds.includes(name))
		const tagsToRemove = initialIds.filter((name) => !updatedIds.includes(name))

		try {
			if (tagsToAdd.length > 0) {
				await addTags(id, tagsToAdd)
			}
			if (tagsToRemove.length > 0) {
				await removeTags(id, tagsToRemove)
			}
			handleClose()
			router.refresh()
		} catch (error) {
			console.error('Ошибка при сохранении тегов:', error)
		}
	}

	return (
		<Modal
			open={isOpen}
			onClose={handleClose}
		>
			<Box
				sx={{
					position: 'absolute',
					top: '50%',
					left: '50%',
					transform: 'translate(-50%, -50%)',
					width: 500,
					bgcolor: 'background.paper',
					boxShadow: 24,
					p: 4,
					borderRadius: 2,
					color: 'black',
					alignItems: 'center',
					display: 'flex',
					flexDirection: 'column',
					gap: '.5rem',
				}}
			>
				<div
					style={{
						display: 'flex',
						gap: '.5rem',
						flexDirection: 'column',
						alignItems: 'center',
						maxWidth: '100%',
					}}
				>
					<div
						style={{
							maxWidth: '320px',
							minWidth: '220px',
							whiteSpace: 'nowrap',
							overflow: 'hidden',
							textOverflow: 'ellipsis',
							textAlign: 'center',
						}}
					>
						{name}
					</div>
					<div
						style={{
							display: 'flex',
							flexDirection: 'row',
							gap: '.5rem',
							alignItems: 'center',
							flexWrap: 'wrap', // добавлено
							justifyContent: 'center',
						}}
					>
						Теги:{' '}
						{localTags.map((tag) => (
							<span
								key={tag.id}
								style={{
									borderRadius: '8px',
									backgroundColor: 'aqua',
									padding: '4px',
									display: 'flex',
									alignItems: 'center',
									gap: '.5rem',
								}}
							>
								{tag.name.length > 4 ? `${tag.name.slice(0, 5)}...` : tag.name}
								<CancelIcon
									onClick={() => handleDeleteTag(tag.id)}
									style={{ cursor: 'pointer' }}
								/>
							</span>
						))}
					</div>
				</div>
				<SelectTags
					onChange={(newTags) => {
						setLocalTags((prev) => {
							const existingIds = new Set(prev.map((tag) => tag.id))
							return [...prev, ...newTags.filter((tag) => !existingIds.has(tag.id))]
						})
					}}
					label='Добавить'
					style={{ width: '100%' }}
				/>

				<Button onClick={handleSaveEdit}>Сохранить</Button>
			</Box>
		</Modal>
	)
}

export default ModalEditFile
