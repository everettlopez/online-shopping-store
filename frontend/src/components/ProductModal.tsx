// This file should have been AdminProductModal
import { useState, useEffect } from "react";
import type { Product } from "../pages/admin/Products";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}

type Category = {
  category_id: number;
  name: string;
  description?: string | null;
};


export default function ProductModal({ isOpen, onClose, product }: Props) {
  if (!isOpen)
  {
    console.log("PRODUCT MODAL CLOSED: ", isOpen);
    return null;
  }

  const isEditing = product !== null;
  const [categories, setCategories] = useState<Category[]>([]);


  useEffect(() => {
    async function loadCategories() {
      const res = await fetch("http://127.0.0.1:8000/api/categories", {
        credentials: "include",
      });

      if (!res.ok) return;

      const data = await res.json();
      setCategories(data.categories as Category[]);
    }

    loadCategories();
  }, []);


  // FORM STATE
  const [form, setForm] = useState({
    name: "",
    category_id: 0,
    price: "",
    size: "",
    color: "",
    image_url: "",
    image_file: null as File | null,

    image_files: [] as File[],   // ⭐ multiple files
    images: [] as string[],
    imagesString: "",
  });

  // PREFILL WHEN EDITING
  useEffect(() => {

    if(!isOpen) return;

    if (product) {
      setForm({
        name: product.name,
        category_id: product.category_id,
        price: String(product.price),
        size: product.size || "",
        color: product.color || "",
        image_url: product.image_url || "",
        image_file: null,

        image_files: [],    
        images: product.images || [],
        imagesString: product.images?.join(", ") || "",

      });
    } else {
      setForm({
        name: "",
        category_id: 0,
        price: "",
        size: "",
        color: "",
        image_url: "",
        image_file: null,
        
        image_files: [],                    
        images: [],
        imagesString: "",
      });
    }
  }, [product, isOpen]);

  // IMAGE PREVIEW
  const previewImage = isEditing
  ? (
      form.images.length > 0
        ? (form.images[0].startsWith("uploads/")
            ? `http://127.0.0.1:8000/${form.images[0]}`
            : form.images[0])
        : form.image_url
    )
  : (
      form.image_file
        ? URL.createObjectURL(form.image_file)
        : form.image_files.length > 0
          ? URL.createObjectURL(form.image_files[0])
          : form.image_url
    );



  // HANDLE FILE UPLOAD
  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] || null;
    setForm({ ...form, image_file: file });
  }

  // SUBMIT HANDLER
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const formData = new FormData();

    const urlImages = form.imagesString
      .split(",")
      .map(s => s.trim())
      .filter(Boolean);

    formData.append("images_urls", JSON.stringify(urlImages));

    // ⭐ Multiple uploaded files
    form.image_files.forEach((file) => {
      formData.append("images_files", file);
    });

    if (form.image_file) {
      formData.append("image", form.image_file);
    } else {
      formData.append("image_url", form.image_url);
    }

    formData.append("name", form.name);
    formData.append("category_id", form.category_id.toString());
    formData.append("price", form.price);
    formData.append("size", form.size);
    formData.append("color", form.color);
    formData.append("description", "");          // keep simple
    formData.append("stock_quantity", "0");      // keep simple
    formData.append("is_active", "true");        // keep simple

    form.image_files.forEach((file) => {
      formData.append("images_files", file);   // ⭐ MUST be "images"
    });


    const method = isEditing ? "PUT" : "POST";
    const url = isEditing
      ? `http://127.0.0.1:8000/api/products/${product!.product_id}`
      : "http://127.0.0.1:8000/api/products";

    const res = await fetch(url, {
      method,
      credentials: "include",
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

        <div className="flex flex-row gap-6">

          {/* LEFT COLUMN */}
          <div className="flex flex-col items-start gap-3">

            {previewImage && (
              <img
                src={previewImage}
                alt="Preview"
                className="w-fit max-h-60 object-cover rounded mb-2"
              />
            )}

            {form.image_files.length > 0 && (
              <div className="grid grid-cols-3 gap-2">
                {form.image_files.map((file, i) => (
                  <img
                    key={i}
                    src={URL.createObjectURL(file)}
                    className="w-20 h-20 object-cover rounded border"
                  />
                ))}
              </div>
            )}

            {form.images.length > 0 && (
              <div className="grid grid-cols-3 gap-2">
                {form.images.map((img, i) => (
                  <img
                    key={i}
                    src={
                      img.startsWith("uploads/")
                        ? `http://127.0.0.1:8000/${img}`
                        : img
                    }
                    className="w-20 h-20 object-cover rounded border"
                  />
                ))}
              </div>
            )}

          </div>

          {/* RIGHT COLUMN — FORM */}
          {/* FORM */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">

            <div className="border border-solid flex flex-col rounded-[10px] p-2">

              <label htmlFor="productName" className="text-gray-400 text-sm">Product Name</label>
              <input
                id="productName"
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="rounded py-2 focus:outline-none focus:ring-0 focus:border-none"
              />
            </div>

            <div className="border border-solid flex flex-col rounded-[10px] p-2">
              <label className="text-gray-400 text-sm">Category</label>

              <select
                value={form.category_id}
                onChange={(e) => setForm({ ...form, category_id: Number(e.target.value) })}
                className="
                  rounded-[8px]
                  py-2
                  bg-white
                  text-gray-700
                  focus:outline-none"
              >
                <option value={0} disabled>Select a category</option>
                {categories.map(cat => (
                  <option key={cat.category_id} value={cat.category_id}>
                    {cat.name}
                  </option>
                ))}
              </select>


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
              multiple
              onChange={(e) => {
                const newFiles = Array.from(e.target.files || []);
                setForm({ ...form, image_files: [...form.image_files, ...newFiles] });
              }}
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
