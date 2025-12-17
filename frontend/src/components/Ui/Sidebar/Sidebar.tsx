'use client'
import { useAuth } from '@/providers/auth/AuthContext'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './styles.module.scss'
import useIdFromParams from '@/hooks/useIdFromParam'
import { ActionButtons } from '@/app/nomenclatures/[id]/components/ActionButtons'
import { Divider } from '@mui/material'
import { useState } from 'react'

const menuItems = [
  { href: '/nomenclatures', label: 'Номенклатуры' },
  { href: '/files', label: 'Файлы' },
  { href: '/playlists', label: 'Плейлисты' },
  {
    label: 'Заказы',
    subItems: [
      { href: '/bgorders', label: 'Фоновые' },
      { href: '/adorders', label: 'Реклама' },
    ],
  },
  { href: '/tasks', label: 'Задачи' },
]

interface ISideBarProps {
  isOpen: boolean
}

const Sidebar = ({ isOpen }: ISideBarProps) => {
  const { isAuthenticated } = useAuth()
  const pathname = usePathname()
  const id = useIdFromParams()
  const [isOrdersOpen, setIsOrdersOpen] = useState(true)

  const isNomenclaturePage = pathname === `/nomenclatures/${id}`
  const isOrdersActive =
    pathname.startsWith('/bgorders') || pathname.startsWith('/adorders')

  return (
    <div className={isOpen ? styles.wrapper_sidebar : styles.sidebar_closed}>
      <div className={styles.sidebar_menu}>
        {menuItems.map((item) => {
          if ('subItems' in item) {
            return (
              <div key={item.label} className={styles.sidebar_submenu__item}>
                <button
                  // onClick={() => setIsOrdersOpen(!isOrdersOpen)}
                  className={`${isAuthenticated ? '' : 'inactive-link'} ${isOrdersActive ? styles.active : ''}`}
                  disabled={!isAuthenticated}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                  }}
                >
                  {item.label}
                  {/* {isOrdersOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />} */}
                </button>

                {isOrdersOpen && (
                  <div className={styles.submenu}>
                    {item.subItems &&
                      item.subItems.map((subItem) => {
                        const isSubActive = pathname.startsWith(subItem.href)
                        return (
                          <Link
                            key={subItem.href}
                            href={isAuthenticated ? subItem.href : '#'}
                            className={`${styles.submenu_item} ${isSubActive ? styles.active : ''}`}
                          >
                            {subItem.label}
                          </Link>
                        )
                      })}
                  </div>
                )}
              </div>
            )
          }

          const isActive = pathname.startsWith(item.href)
          return (
            <div key={item.href} className={styles.sidebar_menu__item}>
              <Link
                href={isAuthenticated ? item.href : '#'}
                className={`${isAuthenticated ? '' : 'inactive-link'} ${isActive ? styles.active : ''}`}
              >
                {item.label}
              </Link>
            </div>
          )
        })}

        {isNomenclaturePage && id && isOpen &&(
          <div style={{
            color: 'black',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            gap: '1rem',
            padding: '0.8rem 1rem',
          }}>
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
