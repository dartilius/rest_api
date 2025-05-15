'use client'

import { useState } from 'react'
import { AdStat } from './adStat/AdStat'
import { HistoryStatistics } from './historyStat/HistoryStatistics'
import { PlayedStatistics } from './playedStat/PlayedStatistics'

const statisticsTabs = [
	{ id: 'history', label: 'История статусов' },
	{ id: 'music', label: 'Музыка' },
	{ id: 'video', label: 'Видео' },
	{ id: 'ad', label: 'Реклама' },
	{ id: 'image', label: 'Картинки' },
	{ id: 'ticker', label: 'Бегущая строка' },
]

export function StatisticsWrapper({ id, className = '' }: { id: string; className?: string }) {
	const [activeTab, setActiveTab] = useState<(typeof statisticsTabs)[number]['id']>('history')

	return (
		<div
			className={`bg-gradient-to-r from-blue-900 via-indigo-900 to-blue-800 rounded-lg shadow ${className}`}
		>
			<div className='border-b border-blue-700'>
				<div className='flex space-x-2 p-2 overflow-x-auto custom_scroll'>
					{statisticsTabs.map((tab) => (
						<button
							key={tab.id}
							onClick={() => setActiveTab(tab.id)}
							className={`px-4 py-2 rounded-md whitespace-nowrap transition-colors ${
								activeTab === tab.id
									? 'bg-white text-blue-900 font-medium'
									: 'text-white hover:bg-blue-800'
							}`}
						>
							{tab.label}
						</button>
					))}
				</div>
			</div>
			<div className='p-4'>
				{activeTab === 'history' && <HistoryStatistics id={id} />}
				{activeTab === 'music' && (
					<PlayedStatistics
						id={id}
						type='music'
					/>
				)}
				{activeTab === 'video' && (
					<PlayedStatistics
						id={id}
						type='video'
					/>
				)}
				{activeTab === 'ad' && (
					<AdStat
						id={id}
						className='w-full'
					/>
				)}
				{activeTab === 'image' && (
					<PlayedStatistics
						id={id}
						type='image'
					/>
				)}
				{activeTab === 'ticker' && (
					<PlayedStatistics
						id={id}
						type='ticker'
					/>
				)}
			</div>
		</div>
	)
}
