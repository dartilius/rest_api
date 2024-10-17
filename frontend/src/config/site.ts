export type SiteConfig = typeof siteConfig;
//ссылки на разделы в navBar'е
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
      label: "Плейлисты",
      href: "/playlists",
    },
    {
      label: "Пользователи",
      href: "/users",
    },
    {
      label: "Репликации",
      href: "/tasks",
    },
    {
      label: "Заказы",
      href: "/orders",
    },
  ],
  //TODO: добавить остальные разделы, чтобы переделать потом под мобилку.
  navMenuItems: [
    {
      label: "Номенлкатуры",
      href: "/nomenclatures",
      index: 0,
    },
    {
      label: "Файлы",
      href: "/files",
      index: 1,
    },
    {
      label: "Плейлисты",
      href: "/playlists",
    },
    {
      label: "Пользователи",
      href: "/users",
      index: 2,
    },
    {
      label: "Репликации",
      href: "/tasks",
      index: 6,
    },
    {
      label: "Заказы",
      href: "/orders",
      index: 7,
    },
    {
      label: "Войти",
      href: "/login",
      index: 9,
    },
    {
      label: "Выйти",
      href: "/login",
      index: 10,
    },
  ],
};
