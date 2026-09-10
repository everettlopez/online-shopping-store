import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";

import { useAuth } from "../context/AuthContext";

type Product = {
    product_id: number;
    category_id: number;
    name: string;
    description?: string;
    price: number;
    size?: string;
    color?: string;
    image_url?: string;
    images?: string[];
    stock_quantity: number;
    is_active: boolean;
};

interface Props {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
  cart: Cart | null;
  setCart: React.Dispatch<React.SetStateAction<Cart | null>>;
  handleAddToCart: (product: Product) => Promise<void>;
}

interface CartItem {
    cart_item_id: number;
    product_id: number;
    quantity: number;
    product: Product | null;
}

interface Cart {
    cart_id: number;
    user_id: number;
    items: CartItem[];
}


export default function ProductDetailModal({ isOpen, onClose, product, cart, setCart, handleAddToCart}: Props) {

  if (!isOpen)
  {
    console.log("PRODUCT DETAIL MODAL CLOSED: ", isOpen);
    return null;
  }
  else
  {
    console.log("PRODUCT DETAIL MODEL OPEN: ", isOpen);
  }

  const [mainImage, setMainImage] = useState(product?.image_url);

  useEffect(() => {
    if (product) {
      setMainImage(product.image_url);
    }
  }, [product]);

  if (!isOpen || !product) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50">
      
      <div className="flex gap-8 bg-white p-8 rounded-[12px] w-full max-w-3xl shadow-xl relative max-h-[90vh] overflow-y-auto items-center">

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-black text-xl"
        >
          ×
        </button>

        {/* Main Image & Thumbnail */}
        <div className="flex flex-col items-center justify-center">
          {/* Main Image */}
          <img
            src={mainImage}
            alt={product.name}
            className="mx-auto w-80 h-80 object-cover rounded-[10px] mb-6"
          />

          {/* Thumbnail Gallery */}
          <div className="flex gap-3 mx-auto">
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
        </div>


        {/* Product Info */}
        <div className="flex flex-col">
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
          <button 
            onClick={() => handleAddToCart(product)}
            className="bg-black text-white py-3 rounded-full w-full hover:bg-gray-800 transition">
            Add to Cart
          </button>
        </div>


      </div>
    </div>
  );
}
