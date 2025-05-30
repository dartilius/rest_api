'use client'

import ActionButton from '@/components/Ui/button/ActionButton'
import { Box, Button, Modal, TextField, Typography } from '@mui/material'
import { ChangeEvent, useState } from 'react'
import { useResend, useSendAction, useSendCommand } from './utils'
type ActionButtonsProps = {
	id: string
}

export function ActionButtons({ id }: ActionButtonsProps) {
	const [openModal, setOpenModal] = useState<boolean>(false)
	const [command, setCommand] = useState<string>('')
	const { handleSendCommand } = useSendCommand()
	const { handleResend } = useResend()
	const { handleSendAction } = useSendAction()

	const handleOpenModal = () => {
		setOpenModal(true)
	}

	const handleCloseModal = () => {
		setOpenModal(false)
	}

	return (
		<div>
			<div className='flex flex-col md:flex-row h-[48px] w-full justify-between mt-4 gap-2'>
				<ActionButton
					className='w-full'
					onClick={() => handleResend(id)}
				>
					Переотправка заказов
				</ActionButton>
				<ActionButton
					className='w-full'
					onClick={() => handleSendAction(id, 'update')}
				>
					Обновить
				</ActionButton>
				<ActionButton
					className='w-full'
					onClick={() => handleSendAction(id, 'reboot')}
				>
					Перезапустить
				</ActionButton>
				<ActionButton
					className='w-full'
					onClick={handleOpenModal}
				>
					Выполнить bash команду
				</ActionButton>
			</div>

			{openModal && (
				<Modal
					open={openModal}
					onClose={handleCloseModal}
					aria-labelledby='modal-modal-title'
					aria-describedby='modal-modal-description'
				>
					<Box sx={style}>
						<Typography
							id='modal-modal-title'
							variant='h6'
							component='h2'
						>
							Введите sh команду
						</Typography>
						<TextField
							variant='outlined'
							fullWidth
							onChange={(e: ChangeEvent<HTMLInputElement>) => {
								setCommand(e.target.value)
							}}
							value={command}
							style={{ backgroundColor: 'white', borderRadius: '4px' }}
						/>
						<div style={{ display: 'flex', justifyContent: 'flex-end' }}>
							<Button
								onClick={() =>
									handleSendCommand(id, 'custom', command, handleCloseModal, setCommand)
								}
								variant='contained'
								color='info'
								style={{ maxWidth: '104px', justifyContent: 'center' }}
							>
								Выполнить
							</Button>
						</div>
					</Box>
				</Modal>
			)}
		</div>
	)
}

const style = {
	position: 'absolute',
	top: '50%',
	left: '50%',
	transform: 'translate(-50%, -50%)',
	width: 400,
	bgcolor: 'background.paper',
	border: '2px solid #000',
	boxShadow: 24,
	p: 4,
	color: 'black',
	borderRadius: 4,
	display: 'flex',
	flexDirection: 'column',
	gap: '1rem',
}
