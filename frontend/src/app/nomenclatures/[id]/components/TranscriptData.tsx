type Props = {
  label: string;
  data: string | number | null;
};

const TranscriptData = (props: Props) => {
  const { label, data } = props;

  if (data) {
    return (
      <div className="flex flex-row items-center gap-1">
        <p className="text-md">{label}: </p>
        <p className="text-default-500">{data}</p>
      </div>
    );
  } else {
    return <></>;
  }
};

export default TranscriptData;
