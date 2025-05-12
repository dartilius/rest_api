// 'use client'

// import React, { useState } from 'react'
// import { deleteFile, getFileDetail } from '@/services/FilesService'
// import {
// 	Box,
// 	Button,
// 	Table,
// 	TableBody,
// 	TableCell,
// 	TableContainer,
// 	TableHead,
// 	TableRow,
// 	Collapse,
// 	Fade,
// 	Grow,
// } from '@mui/material'
// import { convertSizeFile } from '@/utils'
// import { useNotification } from '@/hooks/useNotification'
// import styles from './TableListFile.module.scss'
// import { useRouter } from 'next/navigation'
// import IconActions from '@/app/files/components/TableListFile/IconActions'
// import { IFileDetailResponse, IFilesListResponse, ITagResponse } from '@/types/fileTypes'
// import PreviewFile from '@/app/files/components/PreviewFile/PreviewFile'
// import { TransitionGroup } from 'react-transition-group'
// import ModalEditFile from '@/app/files/components/ModalEditFile/ModalEditFile'
// import Link from 'next/link'
// import CustomPagination from '@/components/Ui/Pagination/CustomPagination'
// import FiltersWrapper from '../FilterWrapper/FiltersWrapper'
// import { Label } from '@/components/data-display/Label'
// import { CopyButton } from '@/components/Ui/button/CoppyButton'

// type Props = {
// 	data: IFilesListResponse['results']
// 	count: number
// }

// const columns = [
// 	{ id: 'name', label: 'Название', minWidth: 170, maxWidth: 170 },
// 	{ id: 'size', label: 'Размер', maxWidth: 120, minWidth: 120 },
// 	{ id: 'type', label: 'Тип', maxWidth: 120, minWidth: 120 },
// 	{ id: 'tags', label: 'Теги', maxWidth: 120, minWidth: 120 },
// 	{ id: 'action', label: 'Действие', maxWidth: 120, minWidth: 120 },
// ]

// const TableListFiles = ({ data, count }: Props) => {
// 	const [fileData, setFileData] = useState<Record<string, IFileDetailResponse>>({})
// 	const [openModal, setOpenModal] = useState<boolean>(false)
// 	const [fileName, setFileName] = useState<string>('')
// 	const [fileTags, setFileTags] = useState<Array<ITagResponse>>([])
// 	const [idFile, setIdFile] = useState<string>('')

// 	const { showNotification } = useNotification()
// 	const router = useRouter()

// 	const handleMoreDetails = async (id: string) => {
// 		if (fileData[id]) {
// 			setFileData((prev) => {
// 				const newData = { ...prev }
// 				delete newData[id]
// 				return newData
// 			})
// 		} else {
// 			try {
// 				const res = await getFileDetail(id)
// 				setFileData((prev) => ({ ...prev, [id]: res }))
// 			} catch (err: any) {
// 				showNotification(err, 'error')
// 			}
// 		}
// 	}

// 	const copyToClipboard = (text: string) => {
// 		navigator.clipboard
// 			.writeText(text)
// 			.then(() => showNotification('Hash скопирован!', 'success'))
// 			.catch((err) => showNotification('Не удалось скопировать Hash!', 'error'))
// 	}

// 	const handleDelete = async (id: string) => {
// 		try {
// 			await deleteFile(id)
// 			showNotification('Файл удален!', 'success')
// 			// revalidatePath('/files')
// 			router.refresh()
// 		} catch (error) {
// 			console.log(error)
// 			showNotification('Не удалось удалить фалй', 'error')
// 		}
// 	}

// 	const handleOpenModal = async (id: string) => {
// 		try {
// 			const res = await getFileDetail(id)
// 			setFileName(res.name)
// 			setIdFile(res.id)
// 			setFileTags(res.tags)
// 			setOpenModal(true)
// 		} catch (e: any) {
// 			showNotification(`Не удалось открыть файл ${e}`, 'error')
// 		}
// 	}

// 	const handleCloseModal = () => {
// 		setFileName('')
// 		setIdFile('')
// 		setFileTags([])
// 		setOpenModal(false)
// 	}

// 	return (
// 		<>
// 			<TableContainer
// 				className={styles.custom_scroll}
// 				sx={{
// 					maxWidth: '100%',
// 					maxHeight: '874px',
// 					height: '100%',
// 					borderRadius: '8px',
// 					backgroundColor: 'white',
// 				}}
// 			>
// 				<Box sx={{ position: 'sticky', top: 0, zIndex: 1, backgroundColor: 'white' }}>
// 					<FiltersWrapper />
// 					<Table stickyHeader>
// 						<TableHead>
// 							<TableRow>
// 								{columns.map((column) => (
// 									<TableCell
// 										key={column.id}
// 										align={column.id === 'action' ? 'left' : 'center'}
// 										sx={{ minWidth: column.minWidth, maxWidth: column.maxWidth }}
// 									>
// 										{column.label}
// 									</TableCell>
// 								))}
// 							</TableRow>
// 						</TableHead>
// 					</Table>
// 				</Box>
// 				<Table>
// 					<TableBody>
// 						{data?.map((row: any) => (
// 							<React.Fragment key={row.id}>
// 								<TableRow
// 									hover
// 									role='checkbox'
// 									tabIndex={-1}
// 								>
// 									{columns.map((column) => {
// 										let value = row[column.id]
// 										if (column.id === 'size') value = convertSizeFile(row.size)
// 										if (column.id === 'tags')
// 											value = `${value?.lenght > 1 ? value.join(', ') : value}`
// 										return (
// 											<TableCell
// 												key={column.id}
// 												align={column.id === 'action' ? 'right' : 'center'}
// 											>
// 												<Link
// 													href={`/files/${row.id}`}
// 													target='_blank'
// 												>
// 													{value}
// 												</Link>
// 												{column.id === 'action' && (
// 													<div
// 														style={{
// 															display: 'flex',
// 															flexDirection: 'row',
// 															justifyContent: 'space-between',
// 															maxHeight: '24px',
// 															alignItems: 'center',
// 															marginLeft: '-24px',
// 														}}
// 														key={row.id}
// 													>
// 														<IconActions
// 															toggleCollapse={handleMoreDetails}
// 															id={row.id}
// 															handleDelete={handleDelete}
// 															handleEdit={handleOpenModal}
// 														/>
// 													</div>
// 												)}
// 											</TableCell>
// 										)
// 									})}
// 								</TableRow>
// 								{fileData[row.id] && (
// 									<TableRow>
// 										<TableCell colSpan={columns.length}>
// 											<TransitionGroup>
// 												{fileData[row.id] && (
// 													<Collapse
// 														key={row.id}
// 														timeout={{ enter: 500, exit: 400 }}
// 													>
// 														<Grow
// 															in
// 															timeout={{ enter: 400, exit: 300 }}
// 														>
// 															<Fade
// 																in
// 																timeout={{ enter: 400, exit: 300 }}
// 															>
// 																<Box sx={{ p: 2, backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
// 																	<div
// 																		style={{
// 																			display: 'flex',
// 																			flexDirection: 'row',
// 																			alignItems: 'center',
// 																			justifyContent: 'space-between',
// 																		}}
// 																	>
// 																		<div className={styles.copy}>
// 																			Hash:{' '}
// 																			<CopyButton
// 																				onCopy={() => copyToClipboard(fileData[row.id]?.hash)}
// 																				label={fileData[row.id]?.hash.slice(0, 20) + '...'}
// 																			/>
// 																		</div>
// 																		<div>Дата создания: {fileData[row.id].created}</div>
// 																	</div>

// 																	{(fileData[row.id]?.tags?.length ?? 0) > 1 && (
// 																		<div>
// 																			Теги:{' '}
// 																			{fileData[row.id]?.tags.map((tag) => tag.name).join(', ')}
// 																		</div>
// 																	)}

// 																	<Box
// 																		mt={2}
// 																		display='flex'
// 																		flexDirection='row'
// 																		justifyContent='center'
// 																	>
// 																		{fileData[row.id] && fileData[row.id]?.name ? (
// 																			<PreviewFile
// 																				file={fileData[row.id]}
// 																				fileType={fileData[row.id]?.name ?? ''}
// 																			/>
// 																		) : (
// 																			'Предпросмотр недоступен'
// 																		)}
// 																	</Box>
// 																</Box>
// 															</Fade>
// 														</Grow>
// 													</Collapse>
// 												)}
// 											</TransitionGroup>
// 										</TableCell>
// 									</TableRow>
// 								)}
// 							</React.Fragment>
// 						))}
// 					</TableBody>
// 				</Table>
// 				<CustomPagination totalItems={count} />
// 			</TableContainer>
// 			<ModalEditFile
// 				isOpen={openModal}
// 				name={fileName}
// 				tags={fileTags}
// 				id={idFile}
// 				handleClose={handleCloseModal}
// 			/>
// 		</>
// 	)
// }

// export default TableListFiles
'use client'

import React, { useState } from 'react'
import { deleteFile, getFileDetail } from '@/services/FilesService'
import {
	Box,
	Table,
	TableBody,
	TableCell,
	TableContainer,
	TableHead,
	TableRow,
	Collapse,
	Fade,
	Grow,
	Paper,
} from '@mui/material'
import { convertSizeFile } from '@/utils'
import { useNotification } from '@/hooks/useNotification'
import styles from './TableListFile.module.scss'
import { useRouter } from 'next/navigation'
import IconActions from '@/app/files/components/TableListFile/IconActions'
import { IFileDetailResponse, IFilesListResponse, ITagResponse } from '@/types/fileTypes'
import PreviewFile from '@/app/files/components/PreviewFile/PreviewFile'
import { TransitionGroup } from 'react-transition-group'
import ModalEditFile from '@/app/files/components/ModalEditFile/ModalEditFile'
import Link from 'next/link'
import CustomPagination from '@/components/Ui/Pagination/CustomPagination'
import FiltersWrapper from '../FilterWrapper/FiltersWrapper'
import { Label } from '@/components/data-display/Label'
import { CopyButton } from '@/components/Ui/button/CoppyButton'

type Props = {
	data: IFilesListResponse['results']
	count: number
}

const columns = [
	{ id: 'name', label: 'Название', minWidth: 170, maxWidth: 170 },
	{ id: 'size', label: 'Размер', maxWidth: 120, minWidth: 120 },
	{ id: 'type', label: 'Тип', maxWidth: 120, minWidth: 120 },
	{ id: 'tags', label: 'Теги', maxWidth: 120, minWidth: 120 },
	{ id: 'action', label: 'Действие', maxWidth: 120, minWidth: 120 },
]

const TableListFiles = ({ data, count }: Props) => {
	const [fileData, setFileData] = useState<Record<string, IFileDetailResponse>>({})
	const [openModal, setOpenModal] = useState<boolean>(false)
	const [fileName, setFileName] = useState<string>('')
	const [fileTags, setFileTags] = useState<Array<ITagResponse>>([])
	const [idFile, setIdFile] = useState<string>('')

	const { showNotification } = useNotification()
	const router = useRouter()

	const handleMoreDetails = async (id: string) => {
		if (fileData[id]) {
			setFileData((prev) => {
				const newData = { ...prev }
				delete newData[id]
				return newData
			})
		} else {
			try {
				const res = await getFileDetail(id)
				setFileData((prev) => ({ ...prev, [id]: res }))
			} catch (err: any) {
				showNotification(err, 'error')
			}
		}
	}

	const copyToClipboard = (text: string) => {
		navigator.clipboard
			.writeText(text)
			.then(() => showNotification('Hash скопирован!', 'success'))
			.catch((err) => showNotification('Не удалось скопировать Hash!', 'error'))
	}

	const handleDelete = async (id: string) => {
		try {
			await deleteFile(id)
			showNotification('Файл удален!', 'success')
			// revalidatePath('/files')
			router.refresh()
		} catch (error) {
			console.log(error)
			showNotification('Не удалось удалить фалй', 'error')
		}
	}

	const handleOpenModal = async (id: string) => {
		try {
			const res = await getFileDetail(id)
			setFileName(res.name)
			setIdFile(res.id)
			setFileTags(res.tags)
			setOpenModal(true)
		} catch (e: any) {
			showNotification(`Не удалось открыть файл ${e}`, 'error')
		}
	}

	const handleCloseModal = () => {
		setFileName('')
		setIdFile('')
		setFileTags([])
		setOpenModal(false)
	}

	return (
		<Paper
			elevation={5}
			sx={{ height: '100%' }}
		>
			<Box
				height={'10%'}
				width={'100%'}
				display={'flex'}
				justifyContent={'center'}
				alignItems={'center'}
			>
				<FiltersWrapper />
			</Box>

			<TableContainer
				className={styles.custom_scroll}
				sx={{
					maxWidth: '100%',

					height: '90%',
					borderRadius: '8px',
					backgroundColor: 'white',
				}}
			>
				<Table
					stickyHeader
					aria-label='sticky table'
					className='rounded'
				>
					<TableHead>
						<TableRow>
							{columns.map((column) => (
								<TableCell
									key={column.id}
									align={column.id === 'action' ? 'right' : 'center'}
									sx={{
										minWidth: column.minWidth,
										maxWidth: column.maxWidth,
										width: column.maxWidth,
										fontWeight: 'bold',
										backgroundColor: '#f5f5f5',
										textAlign: 'center',
									}}
								>
									{column.label}
								</TableCell>
							))}
						</TableRow>
					</TableHead>

					<TableBody>
						{data?.map((row: any) => (
							<React.Fragment key={row.id}>
								<TableRow
									hover
									role='checkbox'
									tabIndex={-1}
								>
									{columns.map((column) => {
										let value = row[column.id]
										if (column.id === 'size') value = convertSizeFile(row.size)
										if (column.id === 'tags')
											value = `${value?.length > 1 ? value.join(', ') : value}`

										return (
											<TableCell
												key={column.id}
												align={column.id === 'action' ? 'right' : 'center'}
												sx={{
													minWidth: column.minWidth,
													maxWidth: column.maxWidth,
													width: column.maxWidth,
													overflow: 'hidden',
													textOverflow: 'ellipsis',
													textAlign: 'center',
												}}
											>
												{column.id !== 'action' ? (
													<Link
														href={`/files/${row.id}`}
														target='_blank'
														style={{
															display: 'block',
															width: '100%',
															overflow: 'hidden',
															textOverflow: 'ellipsis',
														}}
													>
														{value}
													</Link>
												) : (
													<div style={{ display: 'flex', width: '100%', justifyContent: 'center' }}>
														<IconActions
															toggleCollapse={handleMoreDetails}
															id={row.id}
															handleDelete={handleDelete}
															handleEdit={handleOpenModal}
														/>
													</div>
												)}
											</TableCell>
										)
									})}
								</TableRow>
								{fileData[row.id] && (
									<TableRow>
										<TableCell colSpan={columns.length}>
											<TransitionGroup>
												<Collapse
													key={row.id}
													timeout={{ enter: 500, exit: 400 }}
												>
													<Grow
														in
														timeout={{ enter: 400, exit: 300 }}
													>
														<Fade
															in
															timeout={{ enter: 400, exit: 300 }}
														>
															<Box sx={{ p: 2, backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
																<div
																	style={{
																		display: 'flex',
																		flexDirection: 'row',
																		alignItems: 'center',
																		justifyContent: 'space-between',
																	}}
																>
																	<div className={styles.copy}>
																		Hash:{' '}
																		<CopyButton
																			onCopy={() => copyToClipboard(fileData[row.id]?.hash)}
																			label={fileData[row.id]?.hash.slice(0, 20) + '...'}
																		/>
																	</div>
																	<div>Дата создания: {fileData[row.id].created}</div>
																</div>

																{(fileData[row.id]?.tags?.length ?? 0) > 1 && (
																	<div>
																		Теги: {fileData[row.id]?.tags.map((tag) => tag.name).join(', ')}
																	</div>
																)}

																<Box
																	mt={2}
																	display='flex'
																	flexDirection='row'
																	justifyContent='center'
																>
																	{fileData[row.id] && fileData[row.id]?.name ? (
																		<PreviewFile
																			file={fileData[row.id]}
																			fileType={fileData[row.id]?.name ?? ''}
																		/>
																	) : (
																		'Предпросмотр недоступен'
																	)}
																</Box>
															</Box>
														</Fade>
													</Grow>
												</Collapse>
											</TransitionGroup>
										</TableCell>
									</TableRow>
								)}
							</React.Fragment>
						))}
					</TableBody>
				</Table>

				<CustomPagination totalItems={count} />
			</TableContainer>
			<ModalEditFile
				isOpen={openModal}
				name={fileName}
				tags={fileTags}
				id={idFile}
				handleClose={handleCloseModal}
			/>
		</Paper>
	)
}

export default TableListFiles
