interface Props 
{
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
}

export default function ConfirmDeleteProductAdmin({ isOpen, onClose, onConfirm })
{
    if (!isOpen) return null;

    return (
        <>
        <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">

            <div className="p-10 bg-white rounded-lg flex flex-col justify-center items-center gap-5">
                <h2 className="text-xl">Confirm Delete</h2>

                <p>Are you sure you want to delete this product?</p>

                <div className="flex w-full justify-between">
                    <button onClick={onClose} className="border px-4 py-1 rounded-full">Close</button>
                    <button onClick={onConfirm} className="bg-red-500 text-white px-4 py-1 rounded-full">Delete</button>
                </div>
            </div>
        </div>
        </>
    );
}