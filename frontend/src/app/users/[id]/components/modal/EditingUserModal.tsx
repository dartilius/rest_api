import React, { useState } from "react";

type Props = {
  roleOld: string;
  emailOld: string;
  phoneNumberOld: string;
};

const EditingUserModal = (props: Props) => {
  const { roleOld, emailOld, phoneNumberOld } = props;
  const [role, setRole] = useState<string>(roleOld);
  const [email, setEmail] = useState<string>(emailOld);
  const [phoneNumber, setPhoneNumber] = useState<string>(phoneNumberOld);

  return <div />;
};

export default EditingUserModal;
