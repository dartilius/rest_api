export type SiteConfig = typeof siteConfig;

export const siteConfig = {
  navItems: [
    {
      label: "Номенлкатуры",
      href: "/nomenclatures",
    },
    {
      label: "Файлы",
      href: "/files",
    },
    {
      label: "Пользователи",
      href: "/users",
    },
    {
      label: "Группы",
      href: "/groups",
    },
    {
      label: "Плейлисты",
      href: "/playlists",
    },
    {
      label: "Репликации",
      href: "/tasks",
    },
    {
      label: "Заказы",
      href: "/orders",
    },
    {
      label: "Статистика",
      href: "/statistic",
    },
  ],
  navMenuItems: [
    {
      label: "Войти",
      href: "/login",
    },
    {
      label: "Выйти",
      href: "/logout",
    },
  ],
};
