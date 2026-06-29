import { useState, useEffect } from "react";
import type { Product } from "../pages/admin/Products";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}

export default function ProductModal({ isOpen, onClose, product }: Props) {
  if (!isOpen) return null;

  const isEditing = product !== null;

  // FORM STATE
  const [form, setForm] = useState({
    name: "",
    price: "",
    size: "",
    color: "",
    image_url: "",
    image_file: null as File | null,
  });

  // PREFILL WHEN EDITING
  useEffect(() => {
    if (product) {
      setForm({
        name: product.name,
        price: String(product.price),
        size: product.size || "",
        color: product.color || "",
        image_url: product.image_url || "",
        image_file: null,
      });
    } else {
      setForm({
        name: "",
        price: "",
        size: "",
        color: "",
        image_url: "",
        image_file: null,
      });
    }
  }, [product]);

  // IMAGE PREVIEW
  const previewImage = form.image_file
    ? URL.createObjectURL(form.image_file)
    : form.image_url;

  // HANDLE FILE UPLOAD
  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] || null;
    setForm({ ...form, image_file: file });
  }

  // SUBMIT HANDLER
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const formData = new FormData();
    formData.append("name", form.name);
    formData.append("price", form.price);
    formData.append("size", form.size);
    formData.append("color", form.color);

    if (form.image_file) {
      formData.append("image", form.image_file);
    } else {
      formData.append("image_url", form.image_url);
    }

    const method = isEditing ? "PUT" : "POST";
    const url = isEditing
      ? `/api/products/${product!.product_id}`
      : "/api/products";

    const res = await fetch(url, {
      method,
      body: formData,
    });

    if (!res.ok) {
      console.error("Failed to save product");
      return;
    }

    onClose();
    window.location.reload();
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">

      {/* ⭐ SCROLL-SAFE MODAL CONTAINER */}
      <div className="bg-white p-8 rounded-lg w-fit shadow-xl max-h-[90vh] overflow-y-auto">

        <h2 className="text-2xl font-semibold mb-4 tracking-wider flex justify-center">
          {isEditing ? "EDIT PRODUCT" : "CREATE NEW PRODUCT"}
        </h2>

        <div className="flex flex-row gap-4">
          {/* ⭐ IMAGE PREVIEW (IMAGE PREVIEWS) (auto-shrinks, never breaks modal) */}
          {previewImage && (
            <img
              src={previewImage}
              alt="Preview"
              className="w-fit max-h-60 object-cover rounded mb-4"
            />
          )}

          {/* FORM */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">

            <div className="border border-solid flex flex-col rounded-[10px] p-2">

              <label htmlFor="productName"className="text-gray-400 text-sm">Product Name</label>
              <input
                id="productName"
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="rounded py-2 focus:outline-none focus:ring-0 focus:border-none"
              />
            </div>

            <div className="border border-solid flex flex-col rounded-[10px] p-2">
              <label htmlFor="price"className="text-gray-400 text-sm">Price</label>
              <input
                id="price"
                type="number"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
                className="rounded py-2 focus:outline-none focus:ring-0 focus:border-none"
              />
            </div>
            
            <div className="border border-solid flex flex-col rounded-[10px] p-2">
              <label htmlFor="size"className="text-gray-400 text-sm">Size</label>
              <input
                id="size"
                type="text"
                value={form.size}
                onChange={(e) => setForm({ ...form, size: e.target.value })}
                className="rounded py-2 focus:outline-none focus:ring-0 focus:border-none"
              />
            </div>

            <div className="border border-solid flex flex-col rounded-[10px] p-2">
              <label htmlFor="color"className="text-gray-400 text-sm">Color</label>
              <input
                id="color"
                type="text"
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
                className="rounded py-2 focus:outline-none focus:ring-0 focus:border-none"
              />
            </div>

            {/* IMAGE URL */}
            <input
              type="text"
              value={form.image_url}
              onChange={(e) =>
                setForm({ ...form, image_url: e.target.value, image_file: null })
              }
              placeholder="Image URL (optional)"
              className="border p-2 rounded"
            />

            {/* FILE UPLOAD */}
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="border p-2 rounded"
            />

            <button
              type="submit"
              className="bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
            >
              {isEditing ? "Save Changes" : "Create Product"}
            </button>
          </form>
        </div>

        <button
          onClick={onClose}
          className="mt-4 text-gray-600 hover:text-black"
        >
          Close
        </button>
      </div>
    </div>
  );
}
