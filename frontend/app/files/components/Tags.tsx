import { Input } from "@nextui-org/react";
import React from "react";

const Tags = () => {
  return (
    <div className="flex w-full flex-wrap md:flex-nowrap gap-4">
      <Input label="Тэги" placeholder="Тэги" type="text" />
    </div>
  );
};

export default Tags;
