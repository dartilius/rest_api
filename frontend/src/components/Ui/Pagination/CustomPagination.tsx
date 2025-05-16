'use client'
import { Theme, useMediaQuery } from '@mui/material'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { RefObject } from 'react'
import CustomPaginationDesktop from './CustomPaginationDesktop'
import CustomPaginationMobile from './CustomPaginationMobile'

const CustomPagination = ({
	totalItems,
	topRef,
}: {
	totalItems: number
	topRef?: RefObject<HTMLDivElement>
}) => {
	const pathname = usePathname()
	const searchParams = useSearchParams()
	const router = useRouter()
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
	const currentPage = Number(searchParams.get('page') || 1)
	const itemsPerPage = Number(searchParams.get('limit')) || 20

	const totalPages = Math.ceil(totalItems / itemsPerPage)

	const isNextButtonDisabled = Number(currentPage) >= totalPages

	const goToPage = (newPage: number) => {
		const params = new URLSearchParams(searchParams)
		params.set('page', newPage.toString())
		router.push(`${pathname}?${params.toString()}`)
	}

	const nextPage = () => {
		return goToPage(currentPage + 1)
	}

	const prevPage = () => {
		return goToPage(currentPage - 1)
	}

	const isPrevButtonDisabled = currentPage === 1
	const goToFirstPage = () => {
		return goToPage(1)
	}

	return (
		<div className='flex items-center justify-center'>
			{isMobile ? (
				<CustomPaginationMobile
					topRef={topRef}
					currentPage={Number(currentPage)}
					totalPages={totalPages}
					prevPage={prevPage}
					nextPage={nextPage}
					isNextButtonDisabled={isNextButtonDisabled}
					isPrevButtonDisabled={isPrevButtonDisabled}
					goToFirstPage={goToFirstPage}
				/>
			) : (
				<CustomPaginationDesktop
					currentPage={Number(currentPage)}
					totalPages={totalPages}
					prevPage={prevPage}
					nextPage={nextPage}
					isNextButtonDisabled={isNextButtonDisabled}
					isPrevButtonDisabled={isPrevButtonDisabled}
				/>
			)}
		</div>
	)
}

export default CustomPagination
