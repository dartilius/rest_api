import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";
import { toastError } from "@/src/utils/toast-error";
import { toastSuccess } from "@/src/utils/toast-success";
import { Button, Modal, ModalBody, ModalContent, ModalFooter, ModalHeader } from "@nextui-org/react";

type Props = {
  id: string;
  close: () => void;
  open: boolean;
};

const DeletingModal = (props: Props) => {
  const { open, close, id } = props;

  const deleteNomenclature = async () => {
    try {
      await nomenclaturesService.deleteById(id);
      setTimeout(() => {
        window.close();
      }, 2000);
      toastSuccess("Номенклатура успешно удалена");
    } catch (err) {
      toastError(err);
    }
  };

  return (
    <div>
      <Modal isOpen={open} onClose={close}>
        <ModalContent>
          <ModalHeader>Удалить?</ModalHeader>
          <ModalBody>Реально удалить?</ModalBody>
          <ModalFooter>
            <Button onClick={() => deleteNomenclature()}>Да</Button>
            <Button onClick={() => close()}>Нет</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default DeletingModal;