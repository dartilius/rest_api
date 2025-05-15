'use client'

import { staticDelete, staticEdit } from '@/styles'
import { IconButton } from '@mui/material'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { deleteNomenclatures } from '../../api'
import { EditNomenclatureWrapper } from '../EditNomenclature'

type NomenclatureActionsProps = {
	id: string
}

export function NomenclatureActions({ id }: NomenclatureActionsProps) {
	const [isEditModalOpen, setIsEditModalOpen] = useState(false)
	const router = useRouter()

	async function handleDelete() {
		try {
			const res = await deleteNomenclatures(id)

			if (res === 204) {
				router.refresh()
			} else {
				console.error('Error during deletion:', res)
			}
		} catch (error) {
			console.error('Error deleting nomenclatures:', error)
		}
	}

	async function handleEdit() {
		setIsEditModalOpen(true)
	}

	return (
		<div>
			<IconButton
				onClick={handleEdit}
				style={{ background: 'none' }}
			>
				<Image
					src={staticEdit}
					alt='edit'
					width={24}
					height={24}
					style={{
						background: 'none',
						transition: 'opacity 0.3s ease',
					}}
				/>
			</IconButton>
			<IconButton onClick={handleDelete}>
				<Image
					src={staticDelete}
					alt='edit'
					width={24}
					height={24}
					style={{
						background: 'none',
						transition: 'opacity 0.3s ease',
					}}
				/>
			</IconButton>
			{isEditModalOpen && (
				<EditNomenclatureWrapper
					id={id}
					open={isEditModalOpen}
					onClose={() => setIsEditModalOpen(false)}
				/>
			)}
		</div>
	)
}
