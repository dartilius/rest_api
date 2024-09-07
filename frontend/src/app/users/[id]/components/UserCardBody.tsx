import Link from "next/link";

type Props = {
  id?: string;
  email?: string;
  phoneNumber?: string;
  role?: string;
  created?: string;
};

const UserCardBody = (props: Props) => {
  const { id, email, phoneNumber, role, created } = props;

  return (
    <>
      <div className="flex flex-row items-center gap-1">
        <p className="text-md">id</p>
        <p className="text-default-500">{id}</p>
      </div>
      <div className="flex flex-row items-center gap-1">
        <p className="text-md">Email</p>
        <p className="text-default-500">
          <Link href={`mailto:${email}`}>{email}</Link>
        </p>
      </div>
      <div className="flex flex-row items-center gap-1">
        <p className="text-md">Телефон</p>
        <p className="text-default-500">
          <Link href={`tel:${phoneNumber}`}>{phoneNumber}</Link>
        </p>
      </div>
      {role && (
        <div className="flex flex-row items-center gap-1">
          <p className="text-md">Роль</p>
          <p className="text-default-500">{role}</p>
        </div>
      )}
      <div className="flex flex-row items-center gap-1">
        <p className="text-md">Создан</p>
        <p className="text-default-500">{created}</p>
      </div>
    </>
  );
};

export default UserCardBody;
