'use client'
import { useAuth } from '@/providers/auth/AuthContext'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './styles.module.scss'
import useIdFromParams from '@/hooks/useIdFromParam'
import { ActionButtons } from '@/app/nomenclatures/[id]/components/ActionButtons'
import { Divider } from '@mui/material'

const menuItems = [
  { href: '/nomenclatures', label: 'Номенклатуры' },
  { href: '/files', label: 'Файлы' },
  { href: '/playlists', label: 'Плейлисты' },
  { href: '/orders', label: 'Заказы' },
  { href: '/tasks', label: 'Задачи' },
]
interface ISideBarProps {
  isOpen: boolean
}
const Sidebar = ({ isOpen }: ISideBarProps) => {
  const { isAuthenticated } = useAuth()
  const pathname = usePathname()
  const id = useIdFromParams()

  const isNomenclaturePage = pathname === `/nomenclatures/${id}`

  return (
    <div className={isOpen ? styles.wrapper_sidebar : styles.sidebar_closed}>

      <div className={styles.sidebar_menu}>
        {menuItems.map((item) => {
          const isActive = pathname.startsWith(item.href)

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

        {isNomenclaturePage && id && (
          <div
            style={{
              color: 'black',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              gap: '1rem',
              padding: '0.8rem 1rem',
            }}
          >
            <Divider color='black' />
            Админ действия
            <ActionButtons id={id} />
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar
