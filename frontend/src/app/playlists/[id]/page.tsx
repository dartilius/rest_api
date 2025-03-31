import PlayListDetailCard from '@/components/play-lists/PlayListDetailCard'
import { getPlayListDetail } from '../api'

interface Props {
  params: {
    id: string
  }
}
export const dynamic = 'force-dynamic'

const PlayListDetail = async ({ params }: Props) => {
  const { id } = await new Promise<{ id: string }>((resolve) => resolve(params))
  try {
    const playListDetail = await getPlayListDetail(id)
    console.log(playListDetail)

    return (
     <PlayListDetailCard  data={playListDetail}/>
    )
  } catch (error) {
    console.error('Error loading order details:', error)
    return (
      <div className='container mx-auto p-4 text-red-500'>
        Error loading playListDetail
      </div>
    )
  }
}

export default PlayListDetail
