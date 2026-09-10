export default function AddressModal({ isOpen, onClose, onSaved }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg w-full max-w-md shadow-xl relative">

        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-xl"
        >
          ×
        </button>

        <h2 className="text-2xl font-semibold mb-4">Add Address</h2>

        {/* form goes here */}
      </div>
    </div>
  );
}
