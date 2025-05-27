'use client'

import { useNotification } from '@/hooks/useNotification'
import { ITagResponse, ITagsListResponse } from '@/types/fileTypes'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import {
	Box,
	Button,
	Checkbox,
	CircularProgress,
	ListItemText,
	MenuItem,
	Modal,
	OutlinedInput,
	Select,
	TextField,
	Tooltip,
	Zoom,
} from '@mui/material'
import { ChangeEvent, useEffect, useState } from 'react'
import { createTag, getTagList } from '../../api'

interface SelectTagsProps {
	onChange: (tags: ITagResponse[]) => void
	label: string
	style?: React.CSSProperties
}

function SelectTags({ onChange, label, style }: SelectTagsProps) {
	const [tags, setTags] = useState<ITagsListResponse['results']>([])
	const [selectedTags, setSelectedTags] = useState<ITagResponse[]>([])
	const [isOpenModal, setIsOpenModal] = useState(false)
	const [nameValue, setNameValue] = useState('')
	const [currentPage, setCurrentPage] = useState(1)
	const [hasMore, setHasMore] = useState(true)
	const [isLoading, setIsLoading] = useState(false)
	const { showNotification } = useNotification()

	const fetchTags = async (page: number) => {
		if (!hasMore || isLoading) return
		setIsLoading(true)
		try {
			const res = await getTagList(page)
			setTags((prev) => {
				const existingIds = new Set(prev.map((t) => t.id))
				const newUniqueTags = res.results.filter((t) => !existingIds.has(t.id))
				return [...prev, ...newUniqueTags]
			})
			setHasMore(res.next !== null)
			setCurrentPage(page + 1)
		} catch (e: any) {
			showNotification(`Ошибка загрузки тегов: ${e.message}`, 'error')
		} finally {
			setIsLoading(false)
		}
	}

	const handleChange = (event: any) => {
		const selectedIds = event.target.value as string[]
		const updated = tags.filter((tag) => selectedIds.includes(tag.id))
		setSelectedTags(updated)
		onChange(updated)

		// Подгрузка, если выбрали последний тег
		const lastSelectedId = selectedIds[selectedIds.length - 1]
		if (tags.length && tags[tags.length - 1].id === lastSelectedId && hasMore && !isLoading) {
			fetchTags(currentPage)
		}
	}

	const handleSubmit = async () => {
		try {
			const res = await createTag(nameValue)
			showNotification(`Тег ${res.name} с id ${res.id} успешно создан!`, 'success')
			setIsOpenModal(false)
			setNameValue('')
			setTags((prev) => {
				const exists = prev.some((tag) => tag.id === res.id)
				return exists ? prev : [res, ...prev]
			})
		} catch (e: any) {
			showNotification(`Ошибка создания: ${e.message}`, 'error')
		}
	}

	useEffect(() => {
		fetchTags(1)
	}, [])

	return (
		<div style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
			<Select
				multiple
				displayEmpty
				value={selectedTags.map((tag) => tag.id)}
				onChange={handleChange}
				input={<OutlinedInput />}
				renderValue={(selected) => {
					if (selected.length === 0) return `${label} теги`
					return tags
						.filter((tag) => selected.includes(tag.id))
						.map((tag) => tag.name)
						.join(', ')
				}}
				MenuProps={{
					PaperProps: {
						style: {
							maxHeight: 300,
							width: 'auto',
						},
					},
					onScrollCapture: (event: any) => {
						const listboxNode = event.currentTarget
						if (listboxNode.scrollTop + listboxNode.clientHeight >= listboxNode.scrollHeight - 5) {
							fetchTags(currentPage)
						}
					},
				}}
				style={style}
			>
				{tags.map((tag) => (
					<MenuItem
						key={tag.id}
						value={tag.id}
					>
						<Checkbox checked={selectedTags.some((t) => t.id === tag.id)} />
						<ListItemText primary={tag.name} />
					</MenuItem>
				))}
				{isLoading && (
					<MenuItem disabled>
						<CircularProgress size={20} />
					</MenuItem>
				)}
				{!hasMore && tags.length > 0 && (
					<MenuItem disabled>
						<ListItemText primary='Больше тегов нет' />
					</MenuItem>
				)}
			</Select>

			<Tooltip
				title='Создать тег'
				TransitionComponent={Zoom}
				enterDelay={300}
				placement='right'
			>
				<AddCircleOutlineIcon
					style={{ cursor: 'pointer', color: 'var(--primary)' }}
					onClick={() => setIsOpenModal(true)}
				/>
			</Tooltip>

			<Modal
				open={isOpenModal}
				onClose={() => setIsOpenModal(false)}
			>
				<Box
					sx={{
						position: 'absolute',
						top: '50%',
						left: '50%',
						transform: 'translate(-50%, -50%)',
						// width: 500,
						bgcolor: 'background.paper',
						boxShadow: 24,
						p: 4,
						borderRadius: 2,
						color: 'black',
						display: 'flex',
						flexDirection: 'column',
						gap: '.5rem',
					}}
				>
					<div>Создать тег</div>
					<TextField
						variant='outlined'
						fullWidth
						label='Название'
						onChange={(e: ChangeEvent<HTMLInputElement>) => setNameValue(e.target.value)}
						value={nameValue}
						style={{ backgroundColor: 'white', borderRadius: '4px' }}
					/>
					<Button onClick={handleSubmit}>Создать</Button>
				</Box>
			</Modal>
		</div>
	)
}

export default SelectTags
