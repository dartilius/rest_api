import Link from 'next/link'
import Image from 'next/image'
import burgerMenu from '@/styles/img/Navigation/Icon.svg'
import styles from './styles.module.scss'
import AuthButton from '@/components/AuthButton/AuthButton'

type TNavbarProps = {
  toggleSidebar: () => void
}
const Navbar = ({ toggleSidebar }: TNavbarProps) => {
  return (
    <header className={styles.wrapper_navbar}>
      <div className={styles.wrapper_title_navbar}>
        <div className={styles.title}>
          <Link href={'/home'}>RMC ADMIN</Link>
        </div>
        <div className={styles.sidebar_toggle} onClick={toggleSidebar}>
          <Image src={burgerMenu} alt='burgerMenu' width={24} height={24} />
        </div>
      </div>
      <div className={styles.authButton}>
        <AuthButton />
      </div>
    </header>
  )
}
export default Navbar
