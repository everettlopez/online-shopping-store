import { useState } from "react";

export interface Product {
  product_id: number;
  description: string;
  name: string;
  price: number;
  size: string;
  color: string;
  image_url: string;

  // ⭐ Add this:
  images?: string[];
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}


export default function ProductDetailModal({ isOpen, onClose, product }: Props) {
  if (!isOpen || !product) return null;

  const [mainImage, setMainImage] = useState(product.image_url);

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50">
      <div className="bg-white p-8 rounded-[12px] w-full max-w-3xl shadow-xl relative max-h-[90vh] overflow-y-auto">

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-black text-xl"
        >
          ×
        </button>

        {/* Main Image */}
        <img
          src={mainImage}
          alt={product.name}
          className="w-full max-h-[400px] object-cover rounded-[10px] mb-6"
        />

        {/* Thumbnail Gallery */}
        <div className="flex gap-3 mb-6">
          {/* Thumbnail Gallery */}
          {product.images && product.images.length > 0 && (
            <div className="grid grid-cols-3 gap-2 mb-6">
              {product.images.map((img, i) => {
                const src = img.startsWith("uploads/")
                  ? `http://127.0.0.1:8000/${img}`
                  : img;

                return (
                  <img
                    key={i}
                    src={src}
                    onClick={() => setMainImage(src)}
                    className="w-20 h-20 object-cover rounded border cursor-pointer hover:border-black transition"
                  />
                );
              })}
            </div>
          )}

        </div>

        {/* Product Info */}
        <h2 className="text-3xl font-semibold tracking-tight mb-2">
          {product.name}
        </h2>

        <p className="text-xl text-gray-700 mb-4">${product.price}</p>

        <p className="text-gray-600 leading-relaxed mb-6">
          {product.description}
        </p>

        {/* Size & Color */}
        <div className="flex gap-6 text-gray-700 mb-6">
          <p><span className="font-medium">Size:</span> {product.size}</p>
          <p><span className="font-medium">Color:</span> {product.color}</p>
        </div>

        {/* Add to Cart */}
        <button className="bg-black text-white py-3 rounded-full w-full hover:bg-gray-800 transition">
          Add to Cart
        </button>
      </div>
    </div>
  );
}
