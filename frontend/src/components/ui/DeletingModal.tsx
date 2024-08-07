import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@nextui-org/react";

type Props = {
  close: () => void;
  open: boolean;
  deleteProp: () => void;
};

const DeletingModal = (props: Props) => {
  const { open, close, deleteProp } = props;

  return (
    <div>
      <Modal isOpen={open} onClose={close}>
        <ModalContent>
          <ModalHeader>Удалить?</ModalHeader>
          <ModalBody>Реально удалить?</ModalBody>
          <ModalFooter>
            <Button color="danger" onClick={deleteProp}>
              Да
            </Button>
            <Button color="primary" onClick={() => close()}>
              Нет
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default DeletingModal;
