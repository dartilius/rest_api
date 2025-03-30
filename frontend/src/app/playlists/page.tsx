import React from 'react'
import { getPlayLists } from './api'
import PlayLists from '@/components/play-lists/PlayLists'
const PlayListPage = async ({
  searchParams,
}: {
  searchParams?: {
    id: string
    page: number
    limit: number
    name: string
  }
}) => {
  const {
    id = '',
    page = 1,
    limit = 20,
    name = '',
  } = (await searchParams) ?? {}

  const dataPlayList = await getPlayLists({
    id,
    page,
    limit,
    name,
  })

  return <PlayLists dataPlayLists={dataPlayList} />
}
export default PlayListPage
