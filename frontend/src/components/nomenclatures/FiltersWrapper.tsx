'use client'
import FiltersDesktop from '@/components/nomenclatures/filters/FiltersDesktop'
import FiltersMobile from '@/components/nomenclatures/filters/FiltersMobile'
import { Theme, useMediaQuery } from '@mui/material'

export const FiltersWrapper = () => {
	const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))

	return <>{isMobile ? <FiltersMobile /> : <FiltersDesktop />}</>
}
