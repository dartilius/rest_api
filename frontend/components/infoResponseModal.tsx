// components/Modal.js
import React from "react";
import Modal from "react-modal";

// Modal.setAppElement("#__next");

type CustomModalProps = {
  isOpen: boolean;
  onRequestClose: () => void;
  content: string;
};

const CustomModal = (props: CustomModalProps) => {
  const { isOpen, onRequestClose, content } = props;

  return (
    <Modal
      contentLabel="Response Modal"
      isOpen={isOpen}
      style={{
        overlay: {
          backgroundColor: "rgba(0, 0, 0, 0.75)",
        },
        content: {
          top: "50%",
          left: "50%",
          right: "auto",
          bottom: "auto",
          marginRight: "-50%",
          transform: "translate(-50%, -50%)",
        },
      }}
      onRequestClose={onRequestClose}
    >
      <h2>Response</h2>
      <div>{content}</div> {/* Отображение текста ответа */}
      <button onClick={onRequestClose}>Close</button>
    </Modal>
  );
};

export default CustomModal;
