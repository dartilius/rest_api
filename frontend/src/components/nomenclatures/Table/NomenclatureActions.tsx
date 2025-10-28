'use client'

import { staticDelete, staticEdit } from '@/styles'
import { IconButton } from '@mui/material'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { deleteNomenclatures } from '../../../app/nomenclatures/api'
import { EditNomenclatureWrapper } from '../EditNomenclature'

type NomenclatureActionsProps = {
	id: string
	isMobile?: boolean
	onClick?: (e: React.MouseEvent<Element, MouseEvent>) => void
}

export function NomenclatureActions({ id, isMobile }: NomenclatureActionsProps) {
	const [isEditModalOpen, setIsEditModalOpen] = useState(false)
	const router = useRouter()

	async function handleDelete(e: React.MouseEvent) {
		e.stopPropagation()
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

	async function handleEdit(e: React.MouseEvent) {
		e.stopPropagation()
		setIsEditModalOpen(true)
	}

	const handleCloseEditModal = (e?: React.MouseEvent<Element, MouseEvent>) => {
		e?.stopPropagation()
		setIsEditModalOpen(false)
	}

	return (
		<div className={isMobile ? 'z-10' : ''}>
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
					alt='delete'
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
					onClose={handleCloseEditModal}
				/>
			)}
		</div>
	)
}
