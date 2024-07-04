import ReduxToastr from "react-redux-toastr";

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
