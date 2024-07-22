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
      label: "Войти",
      href: "/login",
    },
    {
      label: "Выйти",
      href: "/logout",
    },
  ],
};
