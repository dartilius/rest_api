import ReduxToastr from "react-redux-toastr";

/*
  Компонент ReduxToastrProvider настраивает отображение уведомлений с различными параметрами.
  closeOnToastrClick - Закрытие уведомления при клике на него.
  preventDuplicates - Предотвращение отображения дубликатов уведомлений.
  progressBar - Показывать индикатор прогресса.
  newestOnTop={false} - Старые уведомления будут выше новых.
  timeOut={4000} - Время отображения уведомления в миллисекундах.
  transitionIn="fadeIn" - Переход при появлении уведомления.
  transitionOut="fadeOut" - Переход при исчезновении уведомления.
*/

const ReduxToastrProvider = () => {
  return (
    <ReduxToastr
      closeOnToastrClick
      preventDuplicates
      progressBar
      newestOnTop={false}
      timeOut={4000}
      transitionIn="fadeIn"
      transitionOut="fadeOut"
    />
  );
};

export default ReduxToastrProvider;
