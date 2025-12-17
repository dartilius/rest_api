import Link from 'next/link'
import '../styles/globals.scss'
import notFound from '../styles/img/404.svg'
import Image from 'next/image'

export default function NotFound() {
    return (
        <div className='not-found'>
            <div>
                <Image src={notFound} alt="404" width={400} height={300} />
            </div> {/* svg */}
            <div className='not-found__title'>Страница не найдена</div>
            <Link href="/home" className='not-found__link'>Вернуться на главную</Link>
        </div>
    )
}