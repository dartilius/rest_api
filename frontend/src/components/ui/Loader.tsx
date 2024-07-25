import { Spinner } from "@nextui-org/react";

type Props = {
  loading?: boolean;
};

const Loader = (props: Props) => {
  const { loading } = props;

  return loading ? (
    <div className="flex justify-center">
      <Spinner />
    </div>
  ) : (
    <></>
  );
};

export default Loader;
