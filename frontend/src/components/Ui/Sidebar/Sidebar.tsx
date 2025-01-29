import { useAuth } from "@/providers/auth/AuthContext";
import Link from "next/link";
import { usePathname } from "next/navigation";

const menuItems = [
    { href: "/nomenclatures", label: "Номенклатуры" },
    { href: "/files", label: "Файлы" },
    { href: "/playlists", label: "Плейлисты" },
    { href: "/orders", label: "Заказы" },
    { href: "/tasks", label: "Задачи" },
];

const Sidebar = () => {
    const { isAuthenticated } = useAuth();
    const pathname = usePathname();
    return (
        <div className="sidebar__menu">
            {menuItems.map((item) => (
                <div
                    key={item.href}
                    className={`sidebar__menu-item ${pathname.startsWith(item.href) ? "active" : ""
                        }`}
                >
                    <Link
                        href={isAuthenticated ? item.href : "#"}
                        className={isAuthenticated ? "" : "inactive-link"}
                    >
                        {item.label}
                    </Link>
                </div>
            ))}
        </div>
    )
}

export default Sidebar