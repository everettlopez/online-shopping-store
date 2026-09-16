import Modal from "@mui/material/Modal";

export default function ConfirmDeleteOrderModal({ open, onClose, onConfirm }) {
  return (
    <Modal open={open} onClose={onClose}>
      <div className="bg-white p-6 rounded-lg shadow-xl w-[400px] mx-auto mt-[20vh]">
        <h2 className="text-xl mb-4">Confirm Delete</h2>

        <p className="mb-6">
          Are you sure you want to delete this order?
        </p>

        <div className="flex justify-end gap-4">
          <button
            onClick={onClose}
            className="border px-4 py-2 rounded-full"
          >
            Cancel
          </button>

          <button
            onClick={onConfirm}
            className="bg-red-500 text-white px-4 py-2 rounded-full"
          >
            Delete
          </button>
        </div>
      </div>
    </Modal>
  );
}
