import Modal from "@mui/material/Modal";

interface Props {
  open: boolean;
  message: string;
  onClose: () => void;
  onConfirm: () => void;
}

export default function ConfirmDeleteModal({ open, message, onClose, onConfirm }: Props) {
  return (
    <Modal open={open} onClose={onClose}>
      <div className="bg-white p-6 rounded-lg shadow-xl w-[400px] mx-auto mt-[20vh]">
        <h2 className="text-xl mb-4">Confirm Delete</h2>

        <p className="mb-6">{message}</p>

        <div className="flex justify-end gap-4">
          <button onClick={onClose} className="border px-4 py-2 rounded-full">
            Cancel
          </button>

          <button onClick={onConfirm} className="bg-red-500 text-white px-4 py-2 rounded-full">
            Delete
          </button>
        </div>
      </div>
    </Modal>
  );
}
