import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import UndoIcon from '@mui/icons-material/Undo'

type CustomPaginationMobileProps = {
	currentPage: number
	totalPages: number
	prevPage: () => void
	nextPage: () => void
	isNextButtonDisabled: boolean
	isPrevButtonDisabled: boolean
	goToFirstPage: () => void
}

export default function CustomPaginationMobile({
	currentPage,
	totalPages,
	prevPage,
	nextPage,
	isNextButtonDisabled,
	isPrevButtonDisabled,
	goToFirstPage,
}: CustomPaginationMobileProps) {
	return (
		<>
			<div className='flex items-center justify-evenly bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl p-2 w-fit min-w-[240px] gap-2 min-h-[48px] h-fit rounded-full'>
				<div className='min-w-[48px] text-center text-sm'>
					{currentPage}/{totalPages}
				</div>
				<div className='w-[1px] h-[24px] bg-white/20'></div>
				<button
					className='text-center bg-transparent border-none text-white text-sm font-medium cursor-pointer opacity-70 hover:opacity-100 hover:bg-blue-700 transition-opacity'
					onClick={prevPage}
					disabled={isPrevButtonDisabled}
				>
					<ArrowBackIcon />
				</button>
				<div className='w-[1px] h-[24px] bg-white/20'></div>
				<button
					className='text-center bg-transparent border-none text-white text-sm font-medium cursor-pointer opacity-70 hover:opacity-100 transition-opacity'
					onClick={nextPage}
					disabled={isNextButtonDisabled}
				>
					<ArrowForwardIcon />
				</button>
				<div className='w-[1px] h-[24px] bg-white/20'></div>
				<button
					className='text-center bg-transparent border-none text-white text-sm font-medium cursor-pointer opacity-70 hover:opacity-100 transition-opacity'
					onClick={goToFirstPage}
					disabled={isPrevButtonDisabled}
				>
					<UndoIcon />
				</button>
			</div>
		</>
	)
}
