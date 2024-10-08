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
      label: "Пользователи",
      href: "/users",
      index: 2,
    },
    {
      label: "Группы",
      href: "/groups",
      index: 3,
    },
    {
      label: "Плейлисты",
      href: "/playlists",
      index: 4,
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
      label: "Статистика",
      href: "/statistic",
      index: 8,
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
