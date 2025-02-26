import { useAuth } from '@/providers/auth/AuthContext'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './styles.module.scss'

const menuItems = [
  { href: '/nomenclatures', label: 'Номенклатуры' },
  { href: '/files', label: 'Файлы' },
  { href: '/playlists', label: 'Плейлисты' },
  { href: '/orders', label: 'Заказы' },
  { href: '/tasks', label: 'Задачи' },
]

const Sidebar = () => {
  const { isAuthenticated } = useAuth()
  const pathname = usePathname()
  
  return (
    <div className={styles.wrapper_sidebar}>
      <div className={styles.sidebar_menu}>
        {menuItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          
          return (
            <div key={item.href} className={styles.sidebar_menu__item}>
              <Link
              key={item.href}
                href={isAuthenticated ? item.href : '#'}
                className={`${isAuthenticated ? '' : 'inactive-link'} ${isActive ? styles.active : ''}`}
              >
                {item.label}
              </Link>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Sidebar
