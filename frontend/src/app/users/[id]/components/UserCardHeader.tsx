type Props = {
  firstName?: string;
  middleName?: string;
  lastName?: string;
};

const UserCardHeader = (props: Props) => {
  const { firstName, middleName, lastName } = props;

  return (
    <>
      {firstName && (
        <div className="flex flex-row items-center gap-1">
          <p className="text-md">Имя</p>
          <p className="text-default-500">{firstName}</p>
        </div>
      )}
      {lastName && (
        <div className="flex flex-row items-center gap-1">
          <p className="text-md">Фамилия</p>
          <p className="text-default-500">{lastName}</p>
        </div>
      )}
      {middleName && (
        <div className="flex flex-row items-center gap-1">
          <p className="text-md">Отчество</p>
          <p className="text-default-500">{middleName}</p>
        </div>
      )}
    </>
  );
};

export default UserCardHeader;
